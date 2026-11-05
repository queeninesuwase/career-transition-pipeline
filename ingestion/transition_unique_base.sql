-- Create one career transition row for each pair of successive positions.
--
-- Repeated observations of the same position are reduced to the most
-- recently scraped version before transitions are created.

DROP TABLE IF EXISTS transition_unique_base;

CREATE TABLE transition_unique_base AS
WITH ranked_positions AS (
    SELECT
        ip.*,
        ROW_NUMBER() OVER (
            PARTITION BY USER_ID, POSITION_ID
            ORDER BY SCRAPE_TS DESC, ORDER_IN_PROFILE ASC
        ) AS position_version
    FROM individual_position AS ip
),
latest_positions AS (
    SELECT *
    FROM ranked_positions
    WHERE position_version = 1
      AND STARTDATE IS NOT NULL
),
ordered_positions AS (
    SELECT
        lp.*,
        ROW_NUMBER() OVER (
            PARTITION BY USER_ID
            ORDER BY
                STARTDATE ASC,
                SEQUENCENO ASC,
                ORDER_IN_PROFILE DESC,
                POSITION_ID ASC
        ) AS career_order
    FROM latest_positions AS lp
),
transition_pairs AS (
    SELECT
        previous_position.USER_ID,

        previous_position.SCRAPE_TS AS PREV_SCRAPE_TS,
        previous_position.URI AS PREV_URI,
        previous_position.POSITION_ID AS PREV_POSITION_ID,
        previous_position.COMPANY_RAW AS PREV_COMPANY_RAW,
        previous_position.COMPANYURI AS PREV_COMPANYURI,
        previous_position.TITLE_RAW AS PREV_TITLE_RAW,
        previous_position.LOCATION_RAW AS PREV_LOCATION_RAW,
        previous_position.DESCRIPTION AS PREV_DESCRIPTION,
        previous_position.STARTDATE AS PREV_STARTDATE,
        previous_position.ENDDATE AS PREV_ENDDATE,
        previous_position.SEQUENCENO AS PREV_SEQUENCENO,
        previous_position.ORDER_IN_PROFILE AS PREV_ORDER_IN_PROFILE,
        previous_position.CITY AS PREV_CITY,
        previous_position.STATE AS PREV_STATE,
        previous_position.COUNTRY AS PREV_COUNTRY,
        previous_position.METRO_AREA AS PREV_METRO_AREA,
        previous_position.REGION_NAME AS PREV_REGION_NAME,
        previous_position.RCID AS PREV_RCID,

        new_position.SCRAPE_TS AS NEW_SCRAPE_TS,
        new_position.URI AS NEW_URI,
        new_position.POSITION_ID AS NEW_POSITION_ID,
        new_position.COMPANY_RAW AS NEW_COMPANY_RAW,
        new_position.COMPANYURI AS NEW_COMPANYURI,
        new_position.TITLE_RAW AS NEW_TITLE_RAW,
        new_position.LOCATION_RAW AS NEW_LOCATION_RAW,
        new_position.DESCRIPTION AS NEW_DESCRIPTION,
        new_position.STARTDATE AS NEW_STARTDATE,
        new_position.ENDDATE AS NEW_ENDDATE,
        new_position.SEQUENCENO AS NEW_SEQUENCENO,
        new_position.ORDER_IN_PROFILE AS NEW_ORDER_IN_PROFILE,
        new_position.CITY AS NEW_CITY,
        new_position.STATE AS NEW_STATE,
        new_position.COUNTRY AS NEW_COUNTRY,
        new_position.METRO_AREA AS NEW_METRO_AREA,
        new_position.REGION_NAME AS NEW_REGION_NAME,
        new_position.RCID AS NEW_RCID
    FROM ordered_positions AS previous_position
    JOIN ordered_positions AS new_position
        ON previous_position.USER_ID = new_position.USER_ID
       AND new_position.career_order = previous_position.career_order + 1
)
SELECT *
FROM transition_pairs;