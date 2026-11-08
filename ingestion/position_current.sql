-- Recreate position_current using one latest row for each
-- position slot within a user's profile.
--
-- ROW_NUMBER is used instead of joining only on MAX(SCRAPE_TS)
-- so that if multiple observations have the same latest scrape
-- timestamp, only one deterministic current version is retained.

DROP TABLE IF EXISTS position_current;

CREATE TABLE position_current LIKE position_history;

INSERT INTO position_current
SELECT
    SCRAPE_TS,
    USER_ID,
    URI,
    POSITION_ID,
    COMPANY_RAW,
    COMPANYURI,
    TITLE_RAW,
    LOCATION_RAW,
    DESCRIPTION,
    STARTDATE,
    ENDDATE,
    SEQUENCENO,
    ORDER_IN_PROFILE
FROM (
    SELECT
        ph.*,
        ROW_NUMBER() OVER (
            PARTITION BY
                USER_ID,
                URI,
                ORDER_IN_PROFILE
            ORDER BY
                SCRAPE_TS DESC,
                POSITION_ID DESC
        ) AS current_rank
    FROM position_history AS ph
) AS ranked_positions
WHERE current_rank = 1;