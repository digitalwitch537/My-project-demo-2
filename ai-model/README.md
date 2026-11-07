# MERN AI Root Cause Analysis

The `ai-model` service receives correlated incidents from `aiops`, collects 15 minutes of Prometheus and Loki evidence, asks a local Ollama model for a root-cause analysis, stores the result, and sends the RCA to Slack.

The service is internal-only. It exposes port `8090` on the shared observability network and should not be published directly to the internet.

## Request flow

1. `aiops` correlates at least 5 distinct metric breaches in a 5-minute window and POSTs one incident to `/analyze`.
2. `ai-model` validates the payload and writes a pending job to disk.
3. A background worker collects related metric ranges, the correlated alert timeline, all Docker/system logs, and log clusters for the 15-minute window.
4. Ollama produces a validated JSON analysis using the local model.
5. The worker stores the analysis and sends the RCA to Slack.
6. If Ollama or collection fails, the job is still stored as `fallback`, but no generic RCA is sent to Slack and `notification_skipped_reason` is set to `analysis_fallback`.

`aiops` sends the grouped incident alert. The AI-model notification is the follow-up root-cause message for the same incident ID.

## What gets collected

For every incident, the service collects:

- The triggering metric, all `related_metrics`, and the full correlated alert timeline.
- A Prometheus range query for every Prometheus metric definition.
- A Loki metric range query for every Loki metric definition.
- All logs matching `{job="docker"}` and `{job="system"}`, including application logs.
- Collection errors, which are included in the model prompt instead of being hidden.
- Normalized log clusters that group repeated failure patterns before prompting.

Log lines are truncated, deduplicated, size-limited, and tagged as important when they contain common failure terms. Log content is treated as untrusted data and the system prompt explicitly forbids following instructions found in logs.

## Configuration

The default configuration is `config.yml`:

```yaml
prometheus_url: http://prometheus:9090
loki_url: http://loki:3100
data_dir: /app/data

server:
  host: 0.0.0.0
  port: 8090

worker:
  poll_seconds: 1

collection:
  window_seconds: 900
  step_seconds: 15
  request_timeout_seconds: 15
  max_metric_points: 20
  max_log_lines: 600
  max_log_chars: 30000
  max_log_line_chars: 1200
  log_queries:
    - '{job="docker"}'
    - '{job="system"}'

ollama:
  url: http://ollama:11434
  model: gemma3:4b
  timeout_seconds: 300
  num_ctx: 20480
  num_predict: 1200
  temperature: 0.1
  keep_alive: 5m
```

The `log_queries` list controls which Loki streams are collected. The defaults collect every Docker container log plus system logs. Narrow them if the model context is too small for the deployment.

### Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `AI_MODEL_CONFIG` | `/app/config.yml` | Configuration file path |
| `AI_MODEL_DATA_DIR` | `config.yml` value | Persistent job and result directory |
| `AI_MODEL_HOST` | `0.0.0.0` | HTTP bind address |
| `AI_MODEL_PORT` | `8090` | HTTP port |
| `AI_MODEL_WORKER_POLL_SECONDS` | `1` | Queue polling interval |
| `AI_MODEL_WINDOW_SECONDS` | `900` | Default collection window |
| `AI_MODEL_STEP_SECONDS` | `15` | Prometheus range query step |
| `AI_MODEL_COLLECTION_TIMEOUT_SECONDS` | `15` | Prometheus/Loki request timeout |
| `AI_MODEL_MAX_METRIC_POINTS` | `20` | Points retained per metric series |
| `AI_MODEL_MAX_LOG_LINES` | `600` | Maximum selected log lines |
| `AI_MODEL_MAX_LOG_CHARS` | `30000` | Maximum total log payload size |
| `AI_MODEL_MAX_LOG_LINE_CHARS` | `1200` | Maximum length of one log line |
| `PROMETHEUS_URL` | `http://prometheus:9090` | Prometheus API base URL |
| `LOKI_URL` | `http://loki:3100` | Loki API base URL |
| `GRAFANA_ROOT_URL` | empty | Dashboard link in Slack messages |
| `OLLAMA_URL` | `http://ollama:11434` | Ollama API base URL |
| `OLLAMA_MODEL` | `gemma3:4b` | Ollama model name |
| `OLLAMA_TIMEOUT_SECONDS` | `300` | Ollama request timeout |
| `OLLAMA_NUM_CTX` | `20480` | Model context size |
| `OLLAMA_NUM_PREDICT` | `1200` | Maximum generated tokens |
| `OLLAMA_TEMPERATURE` | `0.1` | Generation temperature |
| `OLLAMA_KEEP_ALIVE` | `5m` | How long Ollama keeps the model loaded |
| `SLACK_ENABLED` | `true` | Enable Slack RCA delivery |
| `SLACK_WEBHOOK_URL` | empty | Slack incoming webhook URL |
| `SLACK_DRY_RUN` | `false` | Log notifications without sending them |
| `SLACK_TIMEOUT_SECONDS` | `10` | Slack request timeout |
| `SLACK_CHANNEL` | empty | Optional Slack channel override |
| `LOG_LEVEL` | `INFO` | Python logging level |

Keep `SLACK_WEBHOOK_URL` out of git. In CI it is supplied from the repository secret `SLACK_WEBHOOK_URL`.

## API

### `POST /analyze`

Accepts an alert and queues an analysis. Repeated `event_id` values are de-duplicated.

```json
{
  "event_id": "incident:incident-1700000000",
  "triggered_at": "2026-01-01T00:06:00+00:00",
  "window_seconds": 900,
  "metric": {
    "id": "api_5xx_rate",
    "title": "API 5xx rate",
    "source": "prometheus",
    "query": "sum(rate(http_requests_total[5m]))",
    "unit": "req/s"
  },
  "result": {
    "status": "critical",
    "value": 12.0,
    "reasons": ["value crossed critical threshold"]
  },
  "related_metrics": [],
  "incident": {
    "id": "incident-1700000000",
    "severity": "critical",
    "metric_count": 5,
    "alerts": [
      {
        "metric": "api_5xx_rate",
        "status": "critical",
        "value": 12.0,
        "timestamp": "2026-01-01T00:01:00+00:00"
      }
    ]
  },
  "grafana_root_url": "http://YOUR_EC2_HOST:3000"
}
```

Response:

```json
{
  "job_id": "0b0f...",
  "status": "queued"
}
```

`status` is `duplicate` when the event was already queued or completed.

### `GET /jobs/{job_id}`

Returns the pending, done, or failed job record. Completed jobs include the analysis, metric evidence, selected logs, collection errors, and whether Slack delivery succeeded.

### `GET /healthz`

Reports the configured model, Ollama URL, pending job count, and default collection window.

## Stored files

All files are written under `AI_MODEL_DATA_DIR`, which is `/app/data` in Docker:

| File | Purpose |
| --- | --- |
| `jobs/pending/*.json` | Queued alerts not yet processed |
| `jobs/done/*.json` | Completed analyses with full results |
| `jobs/failed/*.json` | Jobs that raised an unexpected exception |
| `analyses.jsonl` | Append-only analysis log |
| `failures.jsonl` | Append-only worker failure log |

JSONL files rotate at 5 MB and keep one `.1` backup. Job writes are atomic. The job ID is derived from `event_id`, so duplicate alert delivery is safe.

## Run with Docker

The observability stack must already be running because this service joins the external `mern-observability_observability` network.

```bash
cd ai-model
docker compose up -d ollama
docker compose exec ollama ollama pull gemma3:4b
docker compose up -d --build ai-model
docker compose logs -f ai-model
```

The Ollama model is stored in the `ollama_data` volume, so it survives container recreation. The first pull downloads several gigabytes. A host with at least 8 GB of RAM is recommended for `gemma3:4b`.

If the model is not pulled, jobs complete with `status: fallback`, `notification_skipped_reason: analysis_fallback`, and no generic RCA is posted to Slack. Fix Ollama and submit the incident again or retry the stored job.

Ensure `ai-model/data` is writable by UID/GID `1000` on the host:

```bash
mkdir -p ai-model/data
sudo chown -R 1000:1000 ai-model/data
```

Stop the services:

```bash
cd ai-model
docker compose down
```

Remove the downloaded model volume as well:

```bash
docker compose down -v
```

## Local development

```powershell
cd ai-model
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pytest
```

On Linux or macOS:

```bash
cd ai-model
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

Run against local endpoints:

```powershell
$env:PROMETHEUS_URL = 'http://localhost:9090'
$env:LOKI_URL = 'http://localhost:3100'
$env:OLLAMA_URL = 'http://localhost:11434'
$env:OLLAMA_MODEL = 'gemma3:4b'
$env:SLACK_DRY_RUN = 'true'
$env:AI_MODEL_DATA_DIR = './data'
python main.py
```

## Verification

Submit a test alert:

```powershell
$body = @{
  event_id = 'incident:manual-test-1'
  triggered_at = (Get-Date).ToUniversalTime().ToString('o')
  window_seconds = 900
  metric = @{ id = 'api_5xx_rate'; title = 'API 5xx rate'; source = 'prometheus'; query = 'up'; unit = '' }
  result = @{ status = 'critical'; value = 1; reasons = @('manual test') }
  related_metrics = @()
  incident = @{ id = 'manual-test-1'; severity = 'critical'; metric_count = 1; alerts = @() }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Post -Uri http://localhost:8090/analyze -ContentType 'application/json' -Body $body
```

Then check the job and local files:

```powershell
Invoke-RestMethod http://localhost:8090/healthz
Get-ChildItem ai-model/data/jobs
Get-Content ai-model/data/analyses.jsonl -Tail 1
```

Check Slack without sending a real message:

```powershell
$env:SLACK_DRY_RUN = 'true'
docker compose up -d --force-recreate ai-model
```

## Security notes

- The service is not intended to be exposed publicly. Keep it on the observability Docker network.
- The container runs as a non-root user with `no-new-privileges`.
- Logs and metric labels are untrusted input and are delimited in the prompt.
- The model response is validated as JSON before being stored or sent to Slack.
- Slack has no interactive actions and no credentials beyond the incoming webhook URL.
