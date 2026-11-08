-- Recreate individual_position by enriching position_current
-- with modeled location fields and Revelio company IDs.
--
-- Mapper keys are matched case-sensitively because differently-cased
-- raw strings can map to different modeled values.
--
-- Unmapped locations use empty strings and unmapped companies use RCID 0.

DROP TABLE IF EXISTS individual_position;

CREATE TABLE individual_position LIKE position_current;

ALTER TABLE individual_position
    ADD COLUMN CITY varchar(512),
    ADD COLUMN STATE varchar(512),
    ADD COLUMN COUNTRY varchar(512),
    ADD COLUMN METRO_AREA varchar(512),
    ADD COLUMN REGION_NAME varchar(512),
    ADD COLUMN RCID bigint;

INSERT INTO individual_position
SELECT
    pc.SCRAPE_TS,
    pc.USER_ID,
    pc.URI,
    pc.POSITION_ID,
    pc.COMPANY_RAW,
    pc.COMPANYURI,
    pc.TITLE_RAW,
    pc.LOCATION_RAW,
    pc.DESCRIPTION,
    pc.STARTDATE,
    pc.ENDDATE,
    pc.SEQUENCENO,
    pc.ORDER_IN_PROFILE,
    COALESCE(lm.CITY, ''),
    COALESCE(lm.STATE, ''),
    COALESCE(lm.COUNTRY, ''),
    COALESCE(lm.METRO_AREA, ''),
    COALESCE(lm.REGION_NAME, ''),
    CASE
        WHEN TRIM(COALESCE(pc.COMPANY_RAW, '')) = '' THEN 0
        ELSE COALESCE(c.RCID, 0)
    END
FROM position_current AS pc
LEFT JOIN location_mapper_v3 AS lm
    ON CAST(pc.LOCATION_RAW AS BINARY) = CAST(lm.LOCATION AS BINARY)
LEFT JOIN company2rcid AS c
    ON CAST(pc.COMPANY_RAW AS BINARY) = CAST(c.COMPANY AS BINARY);