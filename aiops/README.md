# MERN AIOps Anomaly Detection

The `aiops` service polls the existing observability stack every 60 seconds, extracts statistical features from each metric, detects abnormal behaviour, correlates related metric breaches into incidents, stores results on disk, and sends Slack alerts when thresholds are crossed.

## What it monitors

The default `config.yml` monitors:

- API request rate
- API 4xx rate
- API 5xx rate
- API 5xx error rate
- API p95 latency
- Node CPU, memory, and disk usage
- Node network receive and transmit
- Backend Prometheus scrape target
- Nginx request rate
- Nginx 5xx error rate
- Nginx p95 latency

Prometheus metrics are queried through the Prometheus HTTP API. Nginx metrics are queried through the Loki HTTP API using LogQL.

## Detection method

For each metric, the service keeps a rolling history in `data/state.json`. Before adding the current sample, it evaluates the sample against the previous history using:

- Rolling mean
- Rolling standard deviation
- Z-score
- Robust z-score using median and median absolute deviation
- Delta from the previous sample
- Rolling minimum and maximum
- Rolling slope

Alerts use two independent signals:

1. Absolute warning and critical thresholds from `config.yml`.
2. Statistical thresholds based on `z_threshold` and `critical_z_threshold`.

A metric must breach for `consecutive_breaches` consecutive checks before an alert is sent. Each metric has a cooldown so Slack is not flooded. A critical upgrade can alert immediately even during a warning cooldown.

The service does not evaluate statistics until `min_samples` baseline samples exist. Until then, results are marked `warming_up`.

## Incident correlation

Correlation is enabled by default. Metric results are collected first, then grouped into an incident candidate:

- A candidate starts when any metric is `breach_due`.
- The candidate is evaluated after `window_seconds` (default `300` seconds).
- At least `min_distinct_metrics` different metrics (default `5`) must have breached.
- Repeated breaches from the same metric count once.
- If fewer than 5 distinct metrics breached, Slack and AI are suppressed and the reason is stored in `state.json` under `correlation.last_suppressed`.
- An incident is emitted at most once per candidate. It remains active until no qualifying metrics are seen for `resolve_after_seconds` (default `300` seconds).
- Up to `max_related_metrics` alerts are included in the grouped message; the rest are counted in `omitted_count`.

When an incident is emitted, `aiops` sends one grouped Slack alert, then triggers one AI RCA with the full incident timeline, all enabled metric definitions, and a 15-minute evidence window. Set `correlation.enabled: false` to restore individual per-metric alerts.

## AI root cause analysis

When an incident is emitted and `ai_model.enabled` is true, `aiops` sends the incident, primary alert, correlated timeline, and all enabled metric definitions to the `ai-model` service. The AI service collects 15 minutes of Prometheus/Loki evidence, including all Docker and system logs, asks a local Ollama model for a root cause, and posts the RCA to Slack.

The AI trigger does not block the incident alert. If `ai-model` is unavailable, the grouped Slack incident alert is still sent, the result includes `ai_model_triggered: false`, and a warning is logged. Set `AI_MODEL_ENABLED=false` when running `aiops` without the AI-model stack.

Each incident gets a deterministic `event_id` of the form `incident:<incident-id>`, so repeated delivery is de-duplicated by the AI service.

## Stored files

All files are written under `AIOPS_DATA_DIR`, which is `/app/data` in Docker:

| File | Purpose |
| --- | --- |
| `state.json` | Rolling history, breach counters, and alert cooldown state used by the next detection cycle |
| `results.jsonl` | One record per metric per 60-second cycle |
| `anomalies.jsonl` | Only warning and critical records |
| `incidents.jsonl` | Emitted correlated incidents with alert delivery and AI trigger status |
| `latest.json` | Latest cycle snapshot, including `incident` when one was emitted |
| `heartbeat.json` | Last successful cycle timestamp |

`state.json` contains metric history plus `correlation.active`, `correlation.candidate`, and `correlation.last_suppressed`. It is written atomically. JSONL files rotate at `results_max_bytes`, `anomalies_max_bytes`, and `incidents_max_bytes`, keeping one `.1` backup per file. A corrupt state file is renamed to `state.corrupt.<timestamp>.json` and detection starts with an empty baseline.

## Configuration

Edit `config.yml` to add, remove, or tune metrics.

```yaml
service:
  poll_interval_seconds: 60
  history_size: 1440
  baseline_window: 60
  min_samples: 15
  consecutive_breaches: 2
  cooldown_seconds: 900

correlation:
  enabled: true
  window_seconds: 300
  min_distinct_metrics: 5
  max_related_metrics: 5
  resolve_after_seconds: 300
  require_critical: false
  suppress_single_alerts: true
```

Metric fields:

```yaml
metrics:
  - id: api_5xx_rate
    title: API 5xx rate
    source: prometheus
    query: 'sum(rate(http_requests_total{job="mern-backend",status=~"5.."}[5m]))'
    unit: req/s
    direction: above
    warning_threshold: 1
    critical_threshold: 5
    z_threshold: 3.0
    critical_z_threshold: 4.5
```

`source` is `prometheus` or `loki`. `direction` is `above`, `below`, or `both`. Set `warning_threshold` or `critical_threshold` to `null` or omit them to use statistical detection only. Metric-level `min_samples`, `baseline_window`, `consecutive_breaches`, and `cooldown_seconds` override the service defaults.

## Environment variables

Copy `.env.example` to `.env` for local Docker use.

| Variable | Default | Purpose |
| --- | --- | --- |
| `PROMETHEUS_URL` | `http://prometheus:9090` | Prometheus API base URL |
| `LOKI_URL` | `http://loki:3100` | Loki API base URL |
| `GRAFANA_ROOT_URL` | empty | Used to build the dashboard link in Slack alerts |
| `AI_MODEL_ENABLED` | `true` | Submit due alerts to the AI-model service |
| `AI_MODEL_URL` | `http://ai-model:8090` | AI-model service base URL |
| `AI_MODEL_TIMEOUT_SECONDS` | `5` | AI-model submission timeout |
| `AI_MODEL_WINDOW_SECONDS` | `900` | Evidence window requested from AI-model |
| `AIOPS_CORRELATION_ENABLED` | `true` | Group related metric breaches into incidents |
| `AIOPS_CORRELATION_WINDOW_SECONDS` | `300` | Seconds to wait before evaluating an incident candidate |
| `AIOPS_CORRELATION_MIN_DISTINCT_METRICS` | `5` | Distinct metrics required for an incident |
| `AIOPS_CORRELATION_MAX_RELATED_METRICS` | `5` | Maximum alerts included in the grouped message |
| `AIOPS_CORRELATION_RESOLVE_AFTER_SECONDS` | `300` | Quiet period before an active incident resolves |
| `SLACK_WEBHOOK_URL` | empty | Slack incoming webhook URL |
| `SLACK_DRY_RUN` | `false` | Log alerts without sending them |
| `SLACK_CHANNEL` | empty | Optional Slack channel override |
| `AIOPS_DATA_DIR` | `/app/data` | Persistent state and result directory |
| `AIOPS_POLL_INTERVAL_SECONDS` | `60` | Detection interval |
| `AIOPS_HISTORY_SIZE` | `1440` | Maximum stored samples per metric |
| `AIOPS_BASELINE_WINDOW` | `60` | Samples used for rolling statistics |
| `AIOPS_MIN_SAMPLES` | `15` | Samples required before statistical evaluation |
| `AIOPS_CONSECUTIVE_BREACHES` | `2` | Consecutive breaches required before alerting |
| `AIOPS_COOLDOWN_SECONDS` | `900` | Minimum seconds between alerts for the same metric |
| `LOG_LEVEL` | `INFO` | Python logging level |

Keep `SLACK_WEBHOOK_URL` out of git. In CI, store it as the GitHub secret `SLACK_WEBHOOK_URL`.

## Run with Docker

The observability stack must be running first because this service joins the external `mern-observability_observability` network. Start `ai-model` before `aiops` when `AI_MODEL_ENABLED=true`.

```bash
cd aiops
docker compose up -d --build
docker compose logs -f aiops
```

The container runs as UID/GID `1000`. Ensure `aiops/data` is writable by that user on the EC2 host.

Stop the service:

```bash
docker compose down
```

## Local development

```bash
cd aiops
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

On Windows PowerShell:

```powershell
cd aiops
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pytest
```

Run against local observability endpoints:

```powershell
$env:PROMETHEUS_URL='http://localhost:9090'
$env:LOKI_URL='http://localhost:3100'
$env:SLACK_DRY_RUN='true'
$env:AI_MODEL_ENABLED='false'
$env:AIOPS_DATA_DIR='./data'
python main.py
```

## Verification

Check the latest cycle:

```bash
cat aiops/data/latest.json
tail -n 5 aiops/data/anomalies.jsonl
tail -n 5 aiops/data/incidents.jsonl
```

Check that the 60-second loop is alive:

```bash
cat aiops/data/heartbeat.json
docker compose -f aiops/docker-compose.yml logs --tail=100 aiops
```

Test Slack without sending a real alert:

```bash
SLACK_DRY_RUN=true docker compose -f aiops/docker-compose.yml up -d --force-recreate aiops
```

When `heartbeat.json` is updating and `results.jsonl` is growing, the detection loop is working. When an incident is emitted, check `latest.json`, `incidents.jsonl`, and `ai_model_triggered`, then inspect `ai-model/data/analyses.jsonl` for the RCA.

## CI deployment

The `ai-model` GitHub Actions job runs after `observability`, copies that folder to `/home/ubuntu/mern/ai-model`, pulls the Ollama model, and starts the AI-model service. The `aiops` job runs after `ai-model`, copies this folder to `/home/ubuntu/mern/aiops`, and starts this Compose service. Add the repository secret `SLACK_WEBHOOK_URL` before enabling Slack delivery for either service.
