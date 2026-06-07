from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


UPSTAGE_BASE_URL = "https://api.upstage.ai/v2"
UPSTAGE_CHAT_COMPLETIONS_URL = "https://api.upstage.ai/v1/chat/completions"
DEFAULT_UPSTAGE_CHAT_MODEL = "solar-pro3"


class SolarClientError(RuntimeError):
    pass


def load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_solar_api_key() -> str | None:
    load_local_env()
    return os.getenv("UPSTAGE_API_KEY") or os.getenv("SOLAR_API_KEY")


def get_upstage_agent_id() -> str:
    load_local_env()
    return os.getenv("UPSTAGE_AGENT_ID", "").strip()


def _request_json(
    *,
    method: str,
    path: str,
    api_key: str,
    payload: dict[str, Any] | None = None,
    query: dict[str, str] | None = None,
    timeout_seconds: int = 20,
) -> dict[str, Any]:
    query_string = f"?{urllib.parse.urlencode(query)}" if query else ""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        f"{UPSTAGE_BASE_URL}{path}{query_string}",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SolarClientError(f"Upstage API request failed: HTTP {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise SolarClientError(f"Upstage API request failed: {exc}") from exc

    return json.loads(raw)


def _extract_output_text(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]

    output = response.get("output", [])
    for item in output:
        for content in item.get("content", []):
            if isinstance(content.get("text"), str):
                return content["text"]

    raise SolarClientError(f"Upstage response does not contain output_text: {response}")


def _parse_json_object(content: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    stripped = content.strip()
    try:
        parsed, _ = decoder.raw_decode(stripped)
    except json.JSONDecodeError as exc:
        raise SolarClientError(f"Upstage returned non-JSON content: {content}") from exc

    if not isinstance(parsed, dict):
        raise SolarClientError(f"Upstage returned JSON that is not an object: {content}")

    if "hard_conditions" in parsed:
        return parsed

    if isinstance(parsed.get("current_state"), dict):
        return parsed["current_state"]

    raise SolarClientError(f"Upstage returned JSON with an unexpected shape: {parsed}")


def call_upstage_agent_json(
    *,
    prompt: str,
    api_key: str | None = None,
    agent_id: str | None = None,
    timeout_seconds: int = 20,
    poll_interval_seconds: int = 2,
    max_polls: int = 10,
) -> dict[str, Any]:
    key = api_key or get_solar_api_key()
    if not key:
        raise SolarClientError("Upstage API key is missing. Set UPSTAGE_API_KEY or SOLAR_API_KEY.")

    payload = {
        "model": agent_id or get_upstage_agent_id(),
        "include": ["last"],
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt,
                    }
                ],
            }
        ],
    }

    response = _request_json(
        method="POST",
        path="/responses",
        api_key=key,
        payload=payload,
        timeout_seconds=timeout_seconds,
    )

    polls = 0
    while response.get("status") in {"queued", "in_progress"} and polls < max_polls:
        time.sleep(poll_interval_seconds)
        response_id = response["id"]
        response = _request_json(
            method="GET",
            path=f"/responses/{response_id}",
            api_key=key,
            query={"include[]": "last"},
            timeout_seconds=timeout_seconds,
        )
        polls += 1

    if response.get("status") != "completed":
        raise SolarClientError(f"Upstage agent response did not complete: {response}")

    content = _extract_output_text(response)

    return _parse_json_object(content)


def call_upstage_chat_json(
    *,
    messages: list[dict[str, str]],
    api_key: str | None = None,
    model: str = DEFAULT_UPSTAGE_CHAT_MODEL,
    timeout_seconds: int = 20,
) -> dict[str, Any]:
    key = api_key or get_solar_api_key()
    if not key:
        raise SolarClientError("Upstage API key is missing. Set UPSTAGE_API_KEY or SOLAR_API_KEY.")

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 1200,
    }
    request = urllib.request.Request(
        UPSTAGE_CHAT_COMPLETIONS_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SolarClientError(f"Upstage chat request failed: HTTP {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise SolarClientError(f"Upstage chat request failed: {exc}") from exc

    data = json.loads(raw)
    content = data["choices"][0]["message"]["content"]

    return _parse_json_object(content)

def call_upstage_chat_content(*, messages, api_key, model, timeout_seconds=20):
    req = urllib.request.Request(
        UPSTAGE_CHAT_COMPLETIONS_URL,
        data=json.dumps({
            "model": model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 1200,
        }).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    return json.loads(
        urllib.request.urlopen(req, timeout=timeout_seconds).read()
    )["choices"][0]["message"]["content"]

def call_upstage_json(
    *,
    prompt: str,
    messages: list[dict[str, str]],
    api_key: str | None = None,
) -> dict[str, Any]:
    agent_id = get_upstage_agent_id()
    if agent_id:
        try:
            return call_upstage_agent_json(prompt=prompt, api_key=api_key, agent_id=agent_id)
        except SolarClientError as exc:
            if "No such agent" not in str(exc):
                raise

    return call_upstage_chat_json(messages=messages, api_key=api_key)