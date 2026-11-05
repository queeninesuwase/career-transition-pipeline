# Part 1: Ingestion
The goal of this part is to start from `position_history`, a table that has the history of all scrapes we've received for certain profiles, and to produce tables that reflect the current state of the profiles, with extra enriched data columns joined in.
## Relevant Tables
| Table Name                                        | Description |
|---------------------------------------------------| ----------- |
| `ingestion.position_history`   | A table containing all historical scraped position data.        | 
| `ingestion.location_mapper_v3` | A modeling output table that contains granular mapped raw location information.
| `ingestion.company2rcid`       | A modeling output table that contains a mapping from company name to RCID (Revelio Company ID).

Please note that for questions A and B, the tables we are asking you to create are already present in the database. You can use them as sanity checks to make sure you are doing the work correctly, but you are still expected to give us a script that recreates them.

For all these problems, we expect a .sql file, or a Python script that executes SQL through the MySQL connector. Please use as many comments as you see fit to explain your work.

### A. Create Position Current
Given the `position_history` table above, please create a `position_current` table, which contains only the "current" position data for each user, disregarding historical scrapes. For each user, it should reflect the most up-to-date version of their profile, with all the positions they have occupied. It should have the same columns as `position_history`.

### B. Create Position Base Table 
Given the `position_current` table you just created, please create `individual_position`, taking all the fields from the raw scrape and adding new ones from the modeling tables: `location_mapper_v3` and `company2rcid`. 

### C. Create Transitions Base Table
Another dataset clients are interested in are users' job transitions between positions, meaning successive positions that a user holds. Please define and explain what should count as a transition, then implement the table. Starting from `individual_position`, please create the `transition_unique_base` table. 

### Transition Definition

A transition is defined as the movement from one unique position to the next position in a user's career history.

Because the same position can appear multiple times across different profile scrapes, repeated observations of the same `USER_ID` and `POSITION_ID` are first reduced to the most recently scraped version.

Positions without a `STARTDATE` are excluded because they cannot be placed reliably in the career timeline.

The remaining positions are ordered primarily by `STARTDATE`. When multiple positions have the same start date, `SEQUENCENO`, `ORDER_IN_PROFILE`, and `POSITION_ID` are used as deterministic tie-breakers.

Each adjacent pair of ordered positions becomes one transition, with the earlier position stored in `PREV_*` fields and the following position stored in `NEW_*` fields. `USER_ID` is stored once because it applies to the whole transition.

The expected format of the table is that each row should contain information about two successive positions. For each field in `individual_position`, if the field is specific to a position, it should appear twice per row: once with a `prev_` prefix and once with a `new_` (referring to the "previous position" and "new position" in the transition). If a field is specific to a user (ex: `user_id`), it should only appear once. 
