from ..step import Step
from ...constants import SCHEMA_TEST, SCHEMA_PROD
from ...utils import execute
from ..table import Table


POSITION_COLS = {
    "SCRAPE_TS",
    "URI",
    "POSITION_ID",
    "COMPANY_RAW",
    "COMPANYURI",
    "TITLE_RAW",
    "LOCATION_RAW",
    "DESCRIPTION",
    "STARTDATE",
    "ENDDATE",
    "SEQUENCENO",
    "ORDER_IN_PROFILE",
    "CITY",
    "STATE",
    "COUNTRY",
    "METRO_AREA",
    "REGION_NAME",
    "RCID"
}


class Transition(Step):
    """
    Create inflow and outflow transition files for selected companies.

    Inflow contains transitions into companies in the input table.
    Outflow contains transitions out of companies in the input table.
    Same-company transitions are excluded.
    """

    def __init__(self, input_table: Step, columns: list[str]):
        super().__init__(key="inflow_file")
        self.input_table = input_table
        self.columns = [col.lower() for col in columns]
        self.source_table = Table(
            "INGESTION.transition_unique_base",
            "INGESTION.transition_unique_base"
        )

    def _process_columns(self):
        processed_cols = []

        for column in self.columns:
            column_upper = column.upper()

            if column_upper == "USER_ID":
                processed_cols.append("A.USER_ID")
            elif column_upper in POSITION_COLS:
                processed_cols.append(f"A.PREV_{column_upper}")
                processed_cols.append(f"A.NEW_{column_upper}")
            else:
                raise Exception(f"Invalid column {column}")

        return ", ".join(processed_cols)

    def _execute(self, cache, debug, test):
        source_table = self.source_table.execute(cache, debug, test)
        input_table = self.input_table.execute(cache, debug, test)

        schema = SCHEMA_TEST if test else SCHEMA_PROD

        inflow_file = f"{schema}.{self.step_id}_inflow_file"
        outflow_file = f"{schema}.{self.step_id}_outflow_file"

        col_str = self._process_columns()

        print(f"""
========== EXECUTING STEP: TRANSITION PIPELINE
Step ID:                {self.step_id}
Input table:            {input_table}
Columns:                {self.columns}
        """)

        if not debug:
            query = f"""
            drop table if exists {inflow_file};
            CREATE TABLE {inflow_file} AS
            SELECT {col_str}
            FROM {source_table} A
            JOIN {input_table} B
            ON A.NEW_RCID = B.RCID
            WHERE A.PREV_RCID <> A.NEW_RCID;

            drop table if exists {outflow_file};
            CREATE TABLE {outflow_file} AS
            SELECT {col_str}
            FROM {source_table} A
            JOIN {input_table} B
            ON A.PREV_RCID = B.RCID
            WHERE A.PREV_RCID <> A.NEW_RCID;
            """

            execute(query)

        return {
            "inflow_file": inflow_file,
            "outflow_file": outflow_file
        }

    def get_parent_step(self):
        return {
            "input_table": self.input_table,
            "source_table": self.source_table
        }

    def update_parent_step(self, new_parent, key=None):
        if key == "source_table":
            self.source_table = new_parent
        else:
            self.input_table = new_parent

    def is_equal(self, other, cache, debug, test) -> bool:
        return self.step_id == other.step_id or (
            isinstance(other, Transition)
            and self.compare_parent_keys(other)
            and set(self.columns) == set(other.columns)
            and self.input_table.is_equal(
                other.input_table,
                cache,
                debug,
                test
            )
        )