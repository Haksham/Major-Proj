# SALF Observability Stack

This project now includes an observability stack for metrics, dashboards, logs, and runtime monitoring.

## Included Services

- `Prometheus`: scrapes backend, ML service, cAdvisor, and node-exporter metrics
- `Grafana`: visualizes metrics and logs
- `Loki`: stores logs
- `Promtail`: ships container logs into Loki
- `cAdvisor`: container-level CPU and memory metrics
- `node-exporter`: host-level CPU, memory, filesystem, and load metrics
- `Alertmanager`: alert routing foundation

## Run The Stack

From the `docker/` directory:

```bash
docker compose up -d prometheus grafana loki promtail node-exporter cadvisor alertmanager nginx
```

To run the full platform including app services:

```bash
docker compose up -d
```

## URLs

- App root: `http://localhost/`
- Report dashboard: `http://localhost/report`
- Grafana: `http://localhost/grafana/`
- Prometheus: `http://localhost:9090`
- Loki API: `http://localhost:3100`
- Alertmanager: `http://localhost:9093`
- cAdvisor: `http://localhost:8088`
- Node Exporter: `http://localhost:9100/metrics`

Grafana default login:

- Username: `admin`
- Password: `${GRAFANA_ADMIN_PASSWORD}` or `admin` if unset

## What To Visualize

### 1. API performance

Open Grafana at `/grafana/` and use the provisioned `SALF Overview` dashboard.

Key panels:

- `Backend Request Rate by Path`
- `Backend P95 Latency by Path`
- `ML P95 Latency by Path`
- `Backend In-Flight Requests`
- `ML In-Flight Requests`

These help explain:

- how many requests the system is handling
- which routes are busiest
- whether latency stays under acceptable thresholds
- whether the ML service is becoming a bottleneck

### 2. Resource usage

Use:

- `Container CPU Usage`
- `Container Memory Usage`
- cAdvisor UI at `http://localhost:8088`

These help show:

- whether backend or ML service is CPU-heavy
- whether model loading increases memory use
- whether container usage spikes during submission/evaluation flows

### 3. Logs

In Grafana, switch to the `Loki` datasource and query logs such as:

```text
{job="docker"}
```

Then narrow by container labels visible in Grafana. This is useful for:

- backend exceptions
- startup failures
- slow request investigation
- ML initialization errors

## Prometheus Endpoints

Prometheus scrapes:

- Backend: `http://backend:8000/prometheus`
- ML service: `http://ml-service:8001/prometheus`

The backend's existing JSON endpoint at `/metrics` remains available for app-level summary data.

## Suggested Demo Flow

1. Open Grafana at `http://localhost/grafana/`
2. Show the `SALF Overview` dashboard
3. Trigger app activity such as login, contribution fetch, or evaluation requests
4. Refresh the dashboard and point to request rate and latency changes
5. Open cAdvisor to show container CPU and memory
6. Open Loki in Grafana Explore to show logs for the same time window

## Same-Domain Public URL

If you are exposing the app through:

```text
https://concert-repeated-outer.ngrok-free.dev
```

set:

```bash
export PUBLIC_BASE_URL=https://concert-repeated-outer.ngrok-free.dev
export GRAFANA_ADMIN_PASSWORD=<strong-password>
```

Then start the full stack from `docker/`:

```bash
docker compose up -d frontend backend ml-service prometheus grafana loki promtail node-exporter cadvisor alertmanager nginx
```

Public routes will be:

- `https://concert-repeated-outer.ngrok-free.dev/`
- `https://concert-repeated-outer.ngrok-free.dev/report`
- `https://concert-repeated-outer.ngrok-free.dev/grafana/`

## Example Performance Story For Report

- Prometheus was used to collect service-level and infrastructure metrics.
- Grafana dashboards were used to visualize request rates, P95 latency, and container resource usage.
- Loki and Promtail were used for centralized log collection and traceable operational debugging.
- cAdvisor and node-exporter were used to observe container and host performance during workload execution.
