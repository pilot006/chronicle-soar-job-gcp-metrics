from SiemplifyJob import SiemplifyJob
import requests
from datetime import datetime, timedelta
import json
import google.auth.transport.requests
from google.oauth2 import service_account
#import sys


INTEGRATION_NAME = "Google Cloud Metrics Loader"
SCRIPT_NAME = "Push Google Cloud Metric to SecOps"

siemplify = SiemplifyJob()
siemplify.script_name = SCRIPT_NAME # In order to use the SiemplifyLogger, you must assign a name to the script.
    
# INIT ACTION PARAMETERS:
gcp_metrics_sa = siemplify.extract_job_param(param_name="Metrics Service Account JSON", print_value=False)
gcp_metrics_sa = json.loads(gcp_metrics_sa)
secops_sa = siemplify.extract_job_param(param_name="SecOps Ingestion API JSON", print_value=False)
secops_sa = json.loads(secops_sa)
project = siemplify.extract_job_param(param_name="GCP Project Name", print_value=True)
metric = siemplify.extract_job_param(param_name="Metric(s)", print_value=True)
customer_id = siemplify.extract_job_param(param_name="SecOps Tenant ID", print_value=True)

log_batch = []


def main():

    try:
        if ',' in metric:
            siemplify.LOGGER.info('Multiple metrics detected in: ' + metric)
            m_arr = metric.split(',')
            for m in m_arr:
                get_metric(m)
        else:
            siemplify.LOGGER.info('Single metric detected in: ' + metric)
            get_metric(metric)

        # If the batch still has lines to send, send them now
        if len(log_batch) > 0:
            send_to_chronicle(log_batch)

    except Exception as e:
        siemplify.LOGGER.error("General error performing job {}".format(SCRIPT_NAME))
        siemplify.LOGGER.exception(e)
        raise

    siemplify.end_script()

def get_metric(metric):
    # Current time
    now = datetime.utcnow()

    # We'll pull data from a -5 minute offset
    offset = now - timedelta(minutes=5)
    offset = datetime.strftime(offset, "%Y-%m-%dT%H:%M:")
    print(offset)

    # Set the start time to 4 minutes from now. This should provide us the most recent metrics
    start_time = now - timedelta(minutes=10)

    # Define the filter for the requested metric
    filter_ = (
        metric
    )

    # URL for Monitoring API endpoint
    url = f"https://monitoring.googleapis.com/v3/projects/{project}/timeSeries?filter={filter_}&interval.startTime={start_time.isoformat()+'Z'}&interval.endTime={now.isoformat()+'Z'}&view=FULL"

    credentials = service_account.Credentials.from_service_account_info(
        gcp_metrics_sa, scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    hdrs = {
        "Authorization": "Bearer " + credentials.token,
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=hdrs)
    siemplify.LOGGER.info("Metrics API response:" + response.text)

    if response.status_code == 200:
        data = json.loads(response.text)
        for time_series in data.get("timeSeries", []):
            p_store = time_series['points']
            time_series['points'] = []
            for p in p_store:
                #print(p)
                if offset in p['interval']['startTime']:
                  time_series['points'].append(p)
                  #print(p)
            #siemplify.LOGGER.info(json.dumps(time_series, indent=1))
            batch_logs(time_series)
            #send_to_chronicle(time_series)
    else:
        print(f"Error: {response.status_code} - {response.text}")

def batch_logs(log_line):
    batch_size = len(json.dumps(log_batch).encode())
    siemplify.LOGGER.info('Batch size: ' + str(batch_size))
    # Batch size is limited to 1 MB: https://cloud.google.com/chronicle/docs/reference/ingestion-api#unstructuredlogentries
    if batch_size < 800000:
        entry = { "log_text": json.dumps(log_line) }
        log_batch.append(entry)
        siemplify.LOGGER.info(json.dumps(log_batch, indent=1))
    else:
        entry = { "log_text": json.dumps(log_line) }
        log_batch.append(entry)
        siemplify.LOGGER.info("Batch full. Sending to Google SecOps.")
        siemplify.LOGGER.info(json.dumps(log_batch, indent=1))
        send_to_chronicle(log_batch)
        log_batch.clear()

def send_to_chronicle(log_lines):
    raw_event = {
        "customer_id": customer_id,
        "log_type": 'UDM',
        "entries": log_lines
    }

    credentials = service_account.Credentials.from_service_account_info(
        secops_sa,
        scopes=['https://www.googleapis.com/auth/malachite-ingestion']
        )
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    hd = {
        "Authorization": "Bearer " + credentials.token,
        "Content-Type": "application/json"
    }
    endpoint = 'https://malachiteingestion-pa.googleapis.com/v2/unstructuredlogentries:batchCreate'
    req = requests.post(endpoint, headers=hd, json=raw_event)
    siemplify.LOGGER.info("Ingest API response:" + req.text)


if __name__ == "__main__":
    main()