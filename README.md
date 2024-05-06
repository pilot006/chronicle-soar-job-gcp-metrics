# Google SecOps SOAR Job - Google Cloud Metrics Loader for SIEM

## Overview
With the [announcement of auto-JSON parsing in Google SecOps](https://cloud.google.com/blog/products/identity-security/introducing-google-security-operations-intel-driven-ai-powered-secops-at-rsa), organizations can now leverage JSON data without the need to build a parser to make the data available. This example job can pull Google Cloud Monitoring metrics in to Google SecOps.

## Pre-requisities
- Google Cloud Project - Metrics are retrieved at a project-level.
- Service Account JSON Key - To retrieve metrics, a service account credential must be created with `monitoring.timeSeries.list` permission.

## Installation
1. Navigate to Releases in this repo and download the .zip package.
2. In Chronicle SOAR/Security Operations, install the integration by opening the IDE and importing the package.
3. Set up a job via the Job Scheduler, providing the project name, service account JSON, and the [metric](https://cloud.google.com/monitoring/api/metrics_gcp) you wish to retrieve.
4. You'll also need to provide your ingestion API credential (JSON format) and your SecOps cutomer ID

## Example
In this example, we're retrieving network utilization metrics for GCE workloads.

![Metrics](gcp-metrics-job.png?raw=true)
