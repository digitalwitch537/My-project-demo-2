from app.collector import (
    LokiRangeClient,
    PrometheusRangeClient,
    collect_logs,
    summarize_series,
)


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code
        self.text = ""

    def json(self) -> dict:
        return self.payload


class FakeSession:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.headers: dict[str, str] = {}
        self.last_params: dict | None = None

    def get(self, url: str, params: dict, timeout: float) -> FakeResponse:
        self.last_params = params
        return FakeResponse(self.payload)


def test_prometheus_range_parsing() -> None:
    session = FakeSession(
        {
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {"job": "mern-backend"},
                        "values": [[1700000000, "1.5"], [1700000015, "2.5"]],
                    }
                ],
            },
        }
    )
    client = PrometheusRangeClient("http://prometheus:9090", 1.0, session=session)

    series = client.query_range("up", 1, 2, 15)

    assert series[0]["labels"]["job"] == "mern-backend"
    assert series[0]["values"][1][1] == 2.5


def test_loki_log_parsing_and_filtering() -> None:
    session = FakeSession(
        {
            "status": "success",
            "data": {
                "resultType": "streams",
                "result": [
                    {
                        "stream": {"container": "mern-backend", "job": "docker"},
                        "values": [
                            ["1700000000000000000", "normal request"],
                            ["1700000001000000000", "ERROR database timeout"],
                        ],
                    }
                ],
            },
        }
    )
    client = LokiRangeClient("http://loki:3100", 1.0, session=session)

    logs = client.query_logs('{job="docker"}', 1, 2, 10)
    selected, errors = collect_logs(client, ('{job="docker"}',), 1, 2, 10, 2000, 300)

    assert len(logs) == 2
    assert not errors
    assert any(entry["important"] for entry in selected)
    assert "database timeout" in selected[-1]["line"]


def test_summarize_series_downsamples() -> None:
    series = {
        "labels": {"job": "test"},
        "values": [(float(index), float(index)) for index in range(20)],
    }

    summary = summarize_series(series, max_points=5)

    assert summary["samples"] == 20
    assert summary["first"] == 0.0
    assert summary["last"] == 19.0
    assert len(summary["points"]) <= 6
