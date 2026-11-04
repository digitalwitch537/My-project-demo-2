from app.ollama_client import OllamaClient


class FakeResponse:
    status_code = 200
    text = ""

    def json(self) -> dict:
        return {"message": {"content": '{"root_cause":"test"}'}}


class FakeSession:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def post(self, url: str, json: dict, timeout: float) -> FakeResponse:
        self.calls.append({"url": url, "json": json, "timeout": timeout})
        return FakeResponse()


def test_ollama_chat_payload_and_response() -> None:
    session = FakeSession()
    client = OllamaClient(
        "http://ollama:11434",
        "gemma3:4b",
        10,
        1024,
        100,
        0.1,
        "5m",
        session=session,
    )

    content = client.chat("system", "user")

    assert content == '{"root_cause":"test"}'
    assert session.calls[0]["json"]["model"] == "gemma3:4b"
    assert session.calls[0]["json"]["format"] == "json"
    assert session.calls[0]["json"]["stream"] is False
