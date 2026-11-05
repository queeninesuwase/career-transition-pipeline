-- Recreate position_current using the latest observed row for each
-- position slot within a user's profile.
--
-- A user can have more than one profile URI, so URI is included in the
-- grouping. ORDER_IN_PROFILE identifies the position's slot in that profile.
-- For each slot, the most recent scrape is treated as the current version.

DROP TABLE IF EXISTS position_current;

CREATE TABLE position_current LIKE position_history;

INSERT INTO position_current
SELECT ph.*
FROM position_history AS ph
JOIN (
    SELECT
        USER_ID,
        URI,
        ORDER_IN_PROFILE,
        MAX(SCRAPE_TS) AS latest_scrape
    FROM position_history
    GROUP BY
        USER_ID,
        URI,
        ORDER_IN_PROFILE
) AS latest_profile_position
    ON ph.USER_ID = latest_profile_position.USER_ID
   AND ph.URI <=> latest_profile_position.URI
   AND ph.ORDER_IN_PROFILE <=> latest_profile_position.ORDER_IN_PROFILE
   AND ph.SCRAPE_TS = latest_profile_position.latest_scrape;