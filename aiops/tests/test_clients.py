import pytest

from app.clients import MetricClientError, PrometheusClient


def client() -> PrometheusClient:
    return PrometheusClient("http://prometheus:9090", 1.0)


def test_parse_vector_result() -> None:
    payload = {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {
                    "metric": {"job": "mern-backend"},
                    "value": [1700000000, "1.25"],
                }
            ],
        },
    }

    sample = client()._parse(payload)

    assert sample is not None
    assert sample.value == pytest.approx(1.25)
    assert sample.labels == {"job": "mern-backend"}


def test_parse_scalar_result() -> None:
    payload = {
        "status": "success",
        "data": {"resultType": "scalar", "result": [1700000000, "42"]},
    }

    sample = client()._parse(payload)

    assert sample is not None
    assert sample.value == pytest.approx(42.0)


def test_parse_empty_vector() -> None:
    payload = {"status": "success", "data": {"resultType": "vector", "result": []}}

    assert client()._parse(payload) is None


def test_parse_rejects_unsupported_result_type() -> None:
    payload = {"status": "success", "data": {"resultType": "matrix", "result": []}}

    with pytest.raises(MetricClientError):
        client()._parse(payload)


def test_parse_rejects_non_numeric_value() -> None:
    payload = {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [{"metric": {}, "value": [1700000000, "not-a-number"]}],
        },
    }

    with pytest.raises(MetricClientError):
        client()._parse(payload)
