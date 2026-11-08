# Revelio Labs Take-Home Assignment

The purpose of this assignment is to recreate parts of the data pipeline that Revelio Labs uses to go from raw data to cleaned, formatted data, eventually delivered to clients. In this case, we will be focusing on profile data (from online platforms such as LinkedIn), and in particular on positions, which are jobs that a user has held and put on their profile.

The assignment has two parts. In the first part (ingestion), you will be working from a table that has a full history of data scrapes, to create tables that will be used as a base for client deliveries. In the second part (deliverables), you will be creating the client deliveries in question.

In order to be able to test your work throughout the assignment, you should have MySQL installed. The installation and setup of MySQL is at your discretion, and the way you go about it will be part of your evaluation. Please detail the steps you took in your submission.

Once you have a MySQL server up and running and you can connect to it, run the commands in `db_setup.sql`, which will create a few empty databases. Then, download this [database dump](https://info0.s3.us-east-2.amazonaws.com/assignment-ds-cfde/ingestion.sql) and import it into the newly created `INGESTION` database.

After all of this is set up, please move to the ingestion section of the assignment. Refer to the `README.md` file inside the `ingestion` folder. Good luck!

---

# Implementation Notes

## Overview

My implementation processes historical profile-position data into:

1. A current-position table.
2. An enriched individual-position table.
3. A career-transition base.
4. Client inflow and outflow deliveries for selected companies.

The work was completed using SQL for ingestion and Python for the deliverables pipeline.

---

## Local MySQL Setup

I used MySQL 8.4 for local development and testing.

I first created the required databases using `db_setup.sql`, then imported the provided ingestion database dump into the `INGESTION` database.

My local portable MySQL instance ran on port `3307`.

During testing, I temporarily configured the Python database connection to use my local port and credentials. Before submission, I restored the original database configuration so that local credentials are not included in the repository.

---

## Provided Inputs

The main provided inputs used in the assignment were:

- `position_history` — historical scraped position records.
- `location_mapper_v3` — mapping from raw location strings to standardized location fields.
- `company2rcid` — mapping from raw company names to Revelio company IDs.
- `position_current_reference` — reference output for current positions.
- `individual_position_reference` — reference output for enriched positions.
- The provided Python deliverables framework.
- Existing classes such as `Step`, `Table`, `CopySQL`, and `CustomTransformStep`.

The transformation SQL itself was not provided. I derived the implementation by analysing the source tables, comparing results with the reference tables, and validating the output.

---

# Part 1: Ingestion

## `position_current`

The purpose of `position_current` is to reduce repeated historical profile observations and retain the latest version of each profile-position slot.

Positions are grouped using:

`USER_ID + URI + ORDER_IN_PROFILE`

Within each group, rows are ranked using `ROW_NUMBER()` and the most recent `SCRAPE_TS` is retained.

`ROW_NUMBER()` is used instead of only joining back to `MAX(SCRAPE_TS)` so that one deterministic row is selected even if more than one candidate has the same latest timestamp.

The current implementation uses:

- `SCRAPE_TS DESC`
- `POSITION_ID DESC`

to select one row from a tied group.

### Reference validation

The generated table contains:

`61,265 rows`

The supplied reference contains:

`61,264 rows`

The row-count comparison showed that every user's row count matches the reference except one user:

`USER_ID 626365796`

My table contains 20 rows for this user while the reference contains 19.

The additional row is an ODT Capital position.

I investigated the difference using:

- `USER_ID`
- `POSITION_ID`
- `SCRAPE_TS`
- profile URI
- company
- title
- start date
- profile order

No duplicate `USER_ID + POSITION_ID + SCRAPE_TS` exists in the provided `position_history` data, and the ODT Capital record appears only once in the latest scrape.

Because I could not reproduce a duplicate from the supplied local data, I did not add a hard-coded rule to remove this individual record simply to match the reference count.

---

## `individual_position`

The `individual_position` table enriches `position_current` with standardized company and location information.

Location information comes from:

`location_mapper_v3`

Company IDs come from:

`company2rcid`

The mapper joins use the available raw company and location values.

When a mapping is unavailable:

- standardized location fields are stored as empty values;
- company `RCID` is stored as `0`.

This makes missing enrichment explicit instead of inventing a mapping that is not present in the provided mapper tables.

### Enrichment validation

The generated table contains:

`61,265 rows`

The supplied reference contains:

`61,264 rows`

The one-row difference comes from the same `position_current` difference described above.

I also compared the enriched values directly against the reference.

Only three shared records differed.

Two records belong to:

`bitWise Academy`

The reference assigns:

`RCID = 18250`

However, the provided local `company2rcid` table contains neither a matching `bitWise Academy` record nor an entry with `RCID = 18250`.

One record has the raw location:

`Gosforth, England, United Kingdom`

The reference contains standardized values for this location, but this exact location is not present in the supplied local `location_mapper_v3` table.

Because these mappings are unavailable in the provided mapper data, I leave them unmatched rather than hard-coding the reference values.

---

## `transition_unique_base`

The `transition_unique_base` table converts individual positions into ordered career transitions.

Before creating transitions, repeated observations of the same:

`USER_ID + POSITION_ID`

are reduced by retaining the most recent scrape.

Positions without a `STARTDATE` are excluded because they cannot be reliably placed in the career timeline.

The remaining positions are ordered using:

1. `STARTDATE ASC`
2. `SEQUENCENO ASC`
3. `ORDER_IN_PROFILE DESC`
4. `POSITION_ID ASC`

The additional fields provide deterministic tie-breaking when multiple positions have the same start date.

After ordering, each position is connected only to the immediately following position.

For example:

`Position 1 → Position 2`

`Position 2 → Position 3`

A direct:

`Position 1 → Position 3`

transition is not created while Position 2 exists between them.

Each transition contains:

- `PREV_*` fields for the previous position.
- `NEW_*` fields for the following position.

---

# Transition Edge Cases

## Overlapping jobs

Overlapping positions are still treated as transitions when one job starts later than another.

For example, if Position B starts after Position A but Position A has not yet ended, the career sequence still contains:

`Position A → Position B`

The transition represents the order in which positions started. It does not require the previous job to have ended first.

---

## Missing start dates

Positions without a `STARTDATE` are removed before the career sequence is created.

This means that if the original data contains:

`Position A → Position B → Position C`

and Position B has no start date, the ordered transition data becomes:

`Position A → Position C`

This is intentional because Position B cannot be reliably placed in the timeline.

---

## Positions with the same start date

Some users have several positions with exactly the same `STARTDATE`.

For example, user `103280857` has multiple positions starting on:

`2020-08-01`

Among them:

- Roblox has `SEQUENCENO = 6`
- Splunk has `SEQUENCENO = 7`
- Jane Street has `SEQUENCENO = 8`

The deterministic ordering therefore begins:

`Roblox → Splunk → Jane Street`

This does not claim that the exact real-world order is known. The available start date is not precise enough to determine that.

The tie-breakers are used so that the pipeline produces a stable and reproducible result.

---

## Transition validation

A previous validation of the transition base produced:

- 54,794 eligible positions
- 6,427 users

For a user with `n` ordered positions, the number of adjacent transitions should be:

`n - 1`

Therefore the expected total was:

`54,794 - 6,427 = 48,367`

The generated table contained:

`48,367 transitions`

Additional checks confirmed that:

- no transition connected a position to itself;
- no transition moved backwards according to the selected ordering.

---

# Part 2: Deliverables

## `Transition` Step

I implemented a `Transition` step inside the provided Python framework.

The step reads from `transition_unique_base` and produces:

- an inflow table;
- an outflow table.

The supplied company input determines which company RCIDs should be included in the delivery.

---

## Inflow

An inflow represents someone joining one of the requested companies.

The main condition is:

`NEW_RCID = requested company RCID`

For example:

`Other Company → Jane Street`

is an inflow into Jane Street.

---

## Outflow

An outflow represents someone leaving one of the requested companies.

The main condition is:

`PREV_RCID = requested company RCID`

For example:

`Jane Street → Other Company`

is an outflow from Jane Street.

---

## Same-company detection

For companies with known RCIDs, company identity is determined using the RCID.

For example:

`Jane Street Analyst → Jane Street Manager`

should not be counted as either an inflow or an outflow.

However, unmatched companies use:

`RCID = 0`

This means two unrelated unmatched companies could otherwise appear as:

`0 → 0`

and incorrectly look like an internal company move.

The implementation therefore uses the following rule:

- If both RCIDs are known, compare the RCIDs.
- If either RCID is unknown (`0`), compare `COMPANY_RAW`.
- Different raw company names are treated as different employers.
- Matching raw company names are treated as the same employer.

For example:

`Unknown Company A → Unknown Company B`

with:

`0 → 0`

is still treated as a real company change.

But:

`Unknown Company A → Unknown Company A`

with:

`0 → 0`

is treated as the same company.

---

## Requested columns

The `Transition` implementation respects the supplied `columns` argument.

For each requested position field, both the previous and new values are included in the delivery using:

`PREV_*`

and:

`NEW_*`

columns.

`USER_ID` is included once.

---

# Testing

I added tests for the `Transition` implementation.

The tests cover:

- entering a requested company;
- leaving a requested company;
- a same-company internal role change;
- transitions unrelated to the requested companies;
- two different unknown companies with `RCID = 0`;
- the same unknown company with `RCID = 0`.

The transition-specific test file currently passes:

`2 passed`

The unknown-company test confirms that:

`Unknown Company A → Unknown Company B`

is treated as a different-company transition, while:

`Unknown Company A → Unknown Company A`

is not.

During earlier full-suite testing, an existing starter-framework test also exposed a local MySQL table-name case-sensitivity difference between:

`INGESTION.LOCATION_MAPPER_V3`

and:

`INGESTION.location_mapper_v3`

This issue is related to the local Linux/MySQL environment rather than the new Transition implementation.

---

# Validation Approach

Throughout the assignment I validated the implementation using:

- row-count comparisons;
- reference-table comparisons;
- duplicate checks;
- per-user row-count comparisons;
- transition-count calculations;
- same-position transition checks;
- backward-transition checks;
- mapper coverage checks;
- controlled unit-test data.

When a difference with a reference could not be reproduced using the supplied source data, I avoided adding one-off hard-coded exceptions simply to force the output to match.

---

# Submission Notes

The submission contains:

- SQL ingestion transformations;
- the Python deliverables framework;
- the implemented `Transition` step;
- Transition unit tests;
- documentation explaining implementation decisions and validation.
