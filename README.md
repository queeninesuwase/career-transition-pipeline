# Revelio Labs Take-Home Assignment

The purpose of this assignment is to recreate parts of the data pipeline that Revelio Labs uses to go from raw data to cleaned, formatted data, eventually delivered to clients. In this case, we will be focusing on profile data (from online platforms such as LinkedIn), and in particular on positions, which are jobs that a user has held and put on their profile.

The assignment has two parts. In the first part (ingestion), you will be working from a table that has a full history of data scrapes, to create tables that will be used as a base for client deliveries. In the second part (deliverables), you will be creating the client deliveries in question.

In order to be able to test your work throughout the assignment, you should have MySQL installed. The installation and setup of MySQL is at your discretion, and the way you go about it will be part of your evaluation. Please detail the steps you took in your submission.

Once you have a MySQL server up and running and you can connect to it, run the commands in `db_setup.sql`, which will create a few empty databases. Then, download this [database dump](https://info0.s3.us-east-2.amazonaws.com/assignment-ds-cfde/ingestion.sql) and import it into the newly created `INGESTION` database.

After all of this is set up, please move to the ingestion section of the assignment. Refer to the `README.md` file inside the `ingestion` folder. Good luck!

---

# Implementation Notes

## Overview

My implementation processes historical job-position data into structured current positions, enriched individual positions, and career transitions. These transitions are then used to identify employee inflows and outflows for selected companies.

The work was completed in two main parts:

1. Reconstructing the required ingestion tables using SQL.
2. Implementing the transition logic inside the provided Python deliverables framework.

## Local MySQL Setup

I used a local MySQL 8.4 installation for development and testing.

I configured a local MySQL instance, created the required databases using `db_setup.sql`, and imported the provided ingestion database dump into the `INGESTION` database.

During local development, the MySQL instance ran on port `3307`. I temporarily configured the Python database connection to use this local port while running the pipeline and tests.

The submitted version retains the original/default connection configuration so that local development credentials are not included in the repository.

## Provided Inputs

The main provided inputs used during the assignment were:

- `position_history` — historical scraped position data.
- `location_mapper_v3` — location mapping information.
- `company2rcid` — mapping between company names and company RCIDs.
- Reference versions of some expected output tables.
- The starter Python deliverables framework.
- Existing classes such as `Step`, `IndividualPosition`, `CopySQL`, and `CustomTransformStep`.

The final SQL transformation rules were not provided directly. I determined them by analysing the source data, comparing generated results with the provided references, and validating the outputs.

## Ingestion

### position_current

The purpose of `position_current` is to reduce repeated profile observations and keep the latest observation of each position slot.

The grouping used is:

`USER_ID + URI + ORDER_IN_PROFILE`

For each group, the record with the most recent `SCRAPE_TS` is retained.

This produced 61,265 rows, while the supplied reference contained 61,264 rows. All shared reference keys matched.

I chose not to add a special-case rule simply to remove the additional row because the general deduplication rule was consistent and reproducible, and the additional record appeared valid.

### individual_position

The `individual_position` table enriches the current positions with standardized company and location information.

Location information is mapped using:

`location_mapper_v3`

Company RCIDs are mapped using:

`company2rcid`

During analysis, I found that company-name casing could affect company mappings. A case-sensitive comparison was therefore used to avoid incorrectly treating differently cased company names as identical.

For missing mappings:

- Location fields are kept empty when a valid location mapping is unavailable.
- `RCID` is set to `0` when a valid company mapping is unavailable.

## transition_unique_base

The `transition_unique_base` table converts individual jobs into career transitions.

Before constructing transitions, repeated observations of the same:

`USER_ID + POSITION_ID`

are reduced by keeping the most recent scrape.

Positions without a `STARTDATE` are excluded because they cannot be placed reliably in a person's career timeline.

The remaining positions are ordered primarily using:

`STARTDATE ASC`

When multiple positions have the same start date, the following fields are used as deterministic tie-breakers:

- `SEQUENCENO ASC`
- `ORDER_IN_PROFILE DESC`
- `POSITION_ID ASC`

These tie-breakers provide a consistent ordering between runs. They are not intended to claim that the fields always represent the true historical sequence.

After ordering each user's positions, the table is self-joined so that each position is connected only to the immediately following position.

For example:

`Position 1 → Position 2`

`Position 2 → Position 3`

A direct:

`Position 1 → Position 3`

transition is not created when Position 2 exists between them.

Each transition contains:

- `PREV_*` fields describing the previous position.
- `NEW_*` fields describing the next position.

## Transition Validation

After deduplication and filtering, there were:

- 54,794 eligible positions.
- 6,427 users.

For a user with `n` ordered positions, the expected number of adjacent transitions is:

`n - 1`

Therefore:

`54,794 - 6,427 = 48,367`

The generated `transition_unique_base` table contained exactly:

`48,367 transitions`

Additional validation confirmed:

- No transition connected a position to itself.
- No backwards career transitions were produced.

## Deliverables

### Transition Step

I added a `Transition` step to the provided Python framework.

The step uses `transition_unique_base` and produces two outputs:

- `INFLOW_FILE`
- `OUTFLOW_FILE`

### Inflow

An inflow represents someone joining one of the requested companies.

The main condition is:

`NEW_RCID = requested company RCID`

For example:

`Other Company → Jane Street`

is an inflow into Jane Street.

### Outflow

An outflow represents someone leaving one of the requested companies.

The main condition is:

`PREV_RCID = requested company RCID`

For example:

`Jane Street → Other Company`

is an outflow from Jane Street.

### Same-Company Transitions

Transitions where:

`PREV_RCID = NEW_RCID`

are excluded from both inflow and outflow.

For example:

`Jane Street Analyst → Jane Street Manager`

represents an internal role change rather than movement into or out of the company.

### Columns

The `Transition` implementation respects the supplied `columns` argument so that the resulting delivery contains the requested fields.

## Testing

I added a unit test for the `Transition` step using controlled sample transitions.

The test covers:

- An employee entering a requested company.
- An employee leaving a requested company.
- A same-company role change.
- A transition unrelated to the requested companies.

The `Transition` test passes successfully.

The complete local test suite produced:

`8 passed, 1 failed`

The remaining failure is from an existing starter-framework test that queries:

`INGESTION.LOCATION_MAPPER_V3`

while the supplied local database contains:

`INGESTION.location_mapper_v3`

The local MySQL environment treats these table names as case-sensitive. The new `Transition` test and the other relevant transformation tests pass successfully.

## Final Pipeline Validation

The final pipeline produced:

- `INDIVIDUAL_POSITION`: 8,516 rows
- `INFLOW_FILE`: 6,261 rows
- `OUTFLOW_FILE`: 3,860 rows

Additional validation confirmed:

- Same-company inflow records: `0`
- Same-company outflow records: `0`
- Invalid inflow companies: `0`
- Invalid outflow companies: `0`

## Submission

The submitted project contains:

- SQL ingestion transformations.
- The Python deliverables framework.
- The `Transition` implementation.
- Unit tests.
- Documentation describing the implementation and validation.

Local virtual environments, cache files, database dumps, Git metadata, and local database credentials are not included in the submitted ZIP.
