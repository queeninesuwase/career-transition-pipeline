from ...transform import CustomTransformStep, Transition
from ....utils import load_df


def create_company_input(output):
    return (
        f"create table {output} (rcid int, company varchar(512));"
        f"insert into {output} values "
        f"(12843, 'Revelio Labs'), "
        f"(8030, 'Jane Street');"
    )


def create_transition_source(output):
    return (
        f"create table {output} ("
        f"USER_ID bigint, "
        f"PREV_CITY varchar(512), "
        f"NEW_CITY varchar(512), "
        f"PREV_TITLE_RAW varchar(512), "
        f"NEW_TITLE_RAW varchar(512), "
        f"PREV_RCID bigint, "
        f"NEW_RCID bigint"
        f");"
        f"insert into {output} values "
        f"(1, 'Boston', 'New York', 'Analyst', 'Engineer', 9999, 8030), "
        f"(2, 'London', 'Boston', 'Engineer', 'Manager', 8030, 9999), "
        f"(3, 'Chicago', 'Chicago', 'Developer', 'Lead', 8030, 8030), "
        f"(4, 'Austin', 'Seattle', 'Developer', 'Engineer', 12843, 8030), "
        f"(5, 'Paris', 'Berlin', 'Analyst', 'Manager', 1111, 2222);"
    )


def test_transition():
    company_input = CustomTransformStep(custom_sql=create_company_input)
    transition_source = CustomTransformStep(custom_sql=create_transition_source)

    transition = Transition(
        input_table=company_input,
        columns=["user_id", "city", "title_raw", "rcid"]
    )

    transition.update_parent_step(
        transition_source,
        key="source_table"
    )

    cache = []

    inflow_file = transition["inflow_file"].execute(
        cache=cache,
        debug=False,
        test=True
    )

    outflow_file = transition["outflow_file"].execute(
        cache=cache,
        debug=False,
        test=True
    )

    inflow = load_df(
        f"SELECT * FROM {inflow_file} ORDER BY USER_ID"
    )

    outflow = load_df(
        f"SELECT * FROM {outflow_file} ORDER BY USER_ID"
    )

    assert list(inflow["USER_ID"]) == [1, 4]
    assert list(outflow["USER_ID"]) == [2, 4]

    expected_columns = {
        "USER_ID",
        "PREV_CITY",
        "NEW_CITY",
        "PREV_TITLE_RAW",
        "NEW_TITLE_RAW",
        "PREV_RCID",
        "NEW_RCID"
    }

    assert set(inflow.columns) == expected_columns
    assert set(outflow.columns) == expected_columns

    assert 3 not in inflow["USER_ID"].values
    assert 3 not in outflow["USER_ID"].values