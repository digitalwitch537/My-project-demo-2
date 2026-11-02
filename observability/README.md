# Observability stack

Grafana, Prometheus, Loki, Promtail, and node-exporter for the MERN app.

## What is collected

- Backend API metrics from `backend:5000/metrics`
- Nginx access-log metrics for all frontend/API traffic
- Frontend, backend, and Mongo container logs through the Docker socket
- Host logs from `/var/log/*.log`
- Host CPU, memory, disk, and network metrics

Nginx metrics are derived from JSON access logs in Loki. There is no separate
nginx Prometheus exporter. Promtail only scrapes the `mern-frontend`,
`mern-backend`, and `mern-mongo` containers so observability logs do not feed
back into Loki.

Promtail is pinned to `3.6.11`, the latest available image. Promtail reached
end of life on March 2, 2026; it is used here as requested. Grafana Alloy is
the successor if you want to migrate later.

## Network requirement

The app compose file names its network `mern_app`. Start the app stack before
this stack:

```bash
cd /home/ubuntu/mern
docker compose -f docker-compose.prod.yml up -d
```

## Manual start

```bash
cd /home/ubuntu/mern/observability
cp .env.example .env
# Set a strong GRAFANA_ADMIN_PASSWORD and the correct GRAFANA_ROOT_URL.
docker compose pull
docker compose up -d
```

Open `http://EC2_HOST:3000`. The default username is `admin`.

The EC2 security group must allow inbound TCP `3000` from your IP. Do not expose
Prometheus, Loki, Promtail, or node-exporter publicly.

## CI deployment

The `observability` GitHub Actions job runs after `deploy`, copies this folder
to `/home/ubuntu/mern/observability`, and starts the stack.

Create a GitHub secret named `GRAFANA_ADMIN_PASSWORD`. The CI job derives
`GRAFANA_ROOT_URL` from `EC2_HOST` unless a different value is supplied.

## Data and retention

- Prometheus metrics: 15 days
- Loki logs: 7 days
- Docker logs: 10 MB x 3 files per container
- Prometheus, Loki, Grafana, and Promtail positions use named volumes

## Verification

```bash
docker compose ps
docker compose logs -f promtail
```

In Grafana, open **MERN Overview**. Check that Prometheus targets are `UP` and
that the application and system log panels return entries.

Backend metrics can be checked from the app network:

```bash
docker run --rm --network mern_app curlimages/curl -s http://backend:5000/metrics | head
```

## Troubleshooting

- `network mern_app not found`: start the app compose stack first.
- Prometheus target down: verify the backend image includes `prom-client` and
  that `/metrics` responds.
- Nginx panels empty: verify the frontend image was rebuilt after the JSON log
  format change, then check Promtail logs for the `mern-frontend` container.
- Docker logs missing: confirm the container names still match the Promtail
  `name` filter (`mern-frontend`, `mern-backend`, `mern-mongo`).
- No system logs: verify `/var/log/*.log` exists on the host and Promtail has
  read access.
- Grafana login redirects to the wrong host: set `GRAFANA_ROOT_URL` in `.env`.
