import requests

from app.ai_model import AiModelClient


class FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.headers: dict[str, str] = {}
        self.calls: list[tuple[str, dict]] = []

    def post(self, url: str, json: dict, timeout: float):
        self.calls.append((url, json))
        return self.response


def test_trigger_posts_payload() -> None:
    session = FakeSession(FakeResponse(202))
    client = AiModelClient("http://ai-model:8090", 1.0, session=session)

    assert client.trigger({"event_id": "abc"}) is True
    assert session.calls[0][0] == "http://ai-model:8090/analyze"
    assert session.calls[0][1]["event_id"] == "abc"


def test_trigger_returns_false_on_http_error() -> None:
    client = AiModelClient(
        "http://ai-model:8090",
        1.0,
        session=FakeSession(FakeResponse(500)),
    )

    assert client.trigger({"event_id": "abc"}) is False
