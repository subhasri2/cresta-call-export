import os
import csv
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import boto3
import clickhouse_connect
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
def get_required_env(name):
    value = os.getenv(name)

    if not value:
        raise ValueError(f"Missing environment variable: {name}")

    return value
def get_export_date():
    """
    Export yesterday's data.
    """

    export_date = (
        datetime.now(timezone.utc) -
        timedelta(days=1)
    ).date()

    return export_date
def get_clickhouse_client():

    client = clickhouse_connect.get_client(
        host=get_required_env("CLICKHOUSE_HOST"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=get_required_env("CLICKHOUSE_USER"),
        password=os.getenv("CLICKHOUSE_PASSWORD", "")
    )

    return client
def build_query():

    query = """
    SELECT
        toDate(call_start) AS export_date,
        customer_id,
        agent_id,

        count() AS total_calls,

        countIf(call_status = 'Answered') AS answered_calls,
        countIf(call_status = 'Missed') AS missed_calls,
        countIf(call_status = 'Rejected') AS rejected_calls,
        countIf(call_status = 'Hangup') AS hangup_calls,
        countIf(call_status = 'Voicemail') AS voicemail_calls,

        round(
            avgIf(call_duration_sec,
            call_status = 'Answered'),
            2
        ) AS avg_answered_call_length_sec,

        quantileIf(
            0.90
        )(
            call_duration_sec,
            call_status = 'Answered'
        ) AS p90_answered_call_length_sec

    FROM conversations

    WHERE customer_id = %(customer_id)s
      AND call_start >= %(start_time)s
      AND call_start < %(end_time)s

    GROUP BY
        export_date,
        customer_id,
        agent_id

    ORDER BY agent_id
    """

    return query
def fetch_daily_metrics(client, customer_id, export_date):
    start_time = datetime.combine(export_date, datetime.min.time())
    end_time = start_time + timedelta(days=1)

    query = build_query()

    result = client.query(
        query,
        parameters={
            "customer_id": customer_id,
            "start_time": start_time,
            "end_time": end_time
        }
    )

    return result.column_names, result.result_rows
def write_csv(column_names, rows, export_date):

    output_dir = Path("output")

    output_dir.mkdir(exist_ok=True)

    file_name = f"agent_call_metrics_{export_date}.csv"

    file_path = output_dir / file_name

    with open(
        file_path,
        mode="w",
        newline="",
        encoding="utf-8"
    ) as csv_file:

        writer = csv.writer(csv_file)

        writer.writerow(column_names)

        writer.writerows(rows)

    return str(file_path)
def upload_to_s3(file_path, export_date):

    bucket = get_required_env("S3_BUCKET")
    prefix = os.getenv("S3_PREFIX", "daily-call-metrics")

    s3_key = f"{prefix}/export_date={export_date}/agent_call_metrics_{export_date}.csv"

    s3_client = boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION", "us-east-1")
    )

    max_attempts = 3

    for attempt in range(1, max_attempts + 1):

        try:
            s3_client.upload_file(file_path, bucket, s3_key)

            logging.info(
                "Uploaded file to s3://%s/%s",
                bucket,
                s3_key
            )

            return

        except Exception:

            logging.exception(
                "S3 upload failed on attempt %s of %s",
                attempt,
                max_attempts
            )

            if attempt == max_attempts:
                raise

            time.sleep(5)

def main():

    try:

        export_date = get_export_date()

        customer_id = get_required_env("CUSTOMER_ID")

        logging.info(
            "Starting export for customer_id=%s date=%s",
            customer_id,
            export_date
        )

        client = get_clickhouse_client()

        column_names, rows = fetch_daily_metrics(
            client,
            customer_id,
            export_date
        )

        logging.info(
            "Fetched %s rows from ClickHouse",
            len(rows)
        )

        if not rows:

            logging.warning(
                "No records found for export date=%s",
                export_date
            )

        csv_path = write_csv(
            column_names,
            rows,
            export_date
        )
        file_size = os.path.getsize(csv_path)

        logging.info(
            "Generated CSV file=%s size=%s bytes",
            csv_path,
            file_size
)

        upload_to_s3(
            csv_path,
            export_date
        )

        logging.info(
            "Export completed successfully"
        )

    except Exception:

        logging.exception(
            "Export job failed"
        )

        logging.error(
            "Alert placeholder: notify Slack/email/monitoring system about export failure"
        )

        raise
if __name__ == "__main__":
    main()