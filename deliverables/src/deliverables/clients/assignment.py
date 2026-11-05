from ..steps import table, transform, delivery
from .client_utils.custom_transforms import generate_input


companies_input = transform.CustomTransformStep(generate_input)


indiv_cols = [
    "SCRAPE_TS",
    "USER_ID",
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
]


transition_cols = [
    "USER_ID",
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
]


individual_position = transform.IndividualPosition(
    companies_input,
    columns=indiv_cols
)


transition = transform.Transition(
    companies_input,
    columns=transition_cols
)


deliveries = [
    delivery.CopySQL(
        individual_position,
        prod_location="DELIVERABLE_OUTPUT.INDIVIDUAL_POSITION",
        test_location="DELIVERABLE_OUTPUT.INDIVIDUAL_POSITION"
    ),
    delivery.CopySQL(
        transition["inflow_file"],
        prod_location="DELIVERABLE_OUTPUT.INFLOW_FILE",
        test_location="DELIVERABLE_OUTPUT.INFLOW_FILE"
    ),
    delivery.CopySQL(
        transition["outflow_file"],
        prod_location="DELIVERABLE_OUTPUT.OUTFLOW_FILE",
        test_location="DELIVERABLE_OUTPUT.OUTFLOW_FILE"
    )
]