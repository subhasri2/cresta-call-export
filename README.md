# Cresta Daily Call Metrics Export

## Overview

This solution exports daily call metrics from ClickHouse, generates a CSV report, and uploads the report to Amazon S3.

The export runs for the previous day's data and aggregates call activity by agent.

## Features

* Connects to ClickHouse
* Retrieves previous day's call metrics
* Calculates:

  * Total Calls
  * Answered Calls
  * Missed Calls
  * Rejected Calls
  * Hangup Calls
  * Voicemail Calls
  * Average Answered Call Length
  * P90 Answered Call Length
* Generates CSV report
* Uploads report to Amazon S3
* Uses environment variables for configuration
* Includes logging and error handling

## Architecture

+-------------+
| ClickHouse  |
+-------------+
       |
       v
+------------------+
| Python Export Job|
+------------------+
       |
       v
+-------------+
| CSV Report  |
+-------------+
       |
       v
+-------------+
| Amazon S3   |
+-------------+

## Project Structure

cresta-call-export/

├── .github/workflows/daily-export.yml

├── export_daily_metrics.py

├── requirements.txt

├── README.md

└── .gitignore

## Environment Variables

CLICKHOUSE_HOST

CLICKHOUSE_PORT

CLICKHOUSE_USER

CLICKHOUSE_PASSWORD

CUSTOMER_ID

S3_BUCKET

S3_PREFIX

AWS_REGION

AWS_ACCESS_KEY_ID

AWS_SECRET_ACCESS_KEY

## Running Locally

1. Create virtual environment

python -m venv .venv

2. Activate virtual environment

.venv\Scripts\activate

3. Install dependencies

pip install -r requirements.txt

4. Configure .env file

5. Run export

python export_daily_metrics.py

## Sample Output

agent_call_metrics_YYYY-MM-DD.csv

The CSV contains agent-level call metrics for the export date.

## Assumptions

* Call data is stored in ClickHouse.
* Reports are generated once per day.
* S3 is used as the destination storage.
* Environment variables contain all required credentials.

## Future Improvements

* Add unit tests
* Add retry logic
* Add monitoring and alerting
* Add support for multiple customers
* Add automated deployment pipeline
