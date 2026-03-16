from __future__ import annotations

import json
import unittest

from maxapi.client.default import DefaultConnectionProperties
from maxapi.transport import RetryPolicy, TransportConfig
from maxapi.transport.client import MaxApiTransport
from maxapi.transport.errors import ResponseDecodeError


class DummyModel:
    def __init__(self, **payload):
        self.payload = payload


class ResponseStub:
    def __init__(self, status: int, payload, headers=None):
        self.status = status
        self._payload = payload
        self.headers = headers or {"Content-Type": "application/json"}
        self.closed = False

    async def json(self, content_type=None):
        del content_type
        if isinstance(self._payload, str):
            return json.loads(self._payload)
        return self._payload

    async def text(self):
        if isinstance(self._payload, str):
            return self._payload
        return json.dumps(self._payload)

    def release(self):
        self.closed = True


class SessionStub:
    def __init__(self, responses):
        self.responses = list(responses)
        self.closed = False
        self.calls = 0

    async def request(self, method, url, **kwargs):
        del method, url, kwargs
        self.calls += 1
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    async def close(self):
        self.closed = True


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_retry_policy_uses_exponential_backoff(self):
        policy = RetryPolicy(initial_delay=0.5, backoff=2.0, max_delay=8.0)
        self.assertEqual(policy.delay_for_attempt(1), 0.5)
        self.assertEqual(policy.delay_for_attempt(2), 1.0)
        self.assertEqual(policy.delay_for_attempt(3), 2.0)
        self.assertEqual(policy.delay_for_attempt(5), 8.0)

    async def test_request_parses_model(self):
        config = TransportConfig.from_default_connection(DefaultConnectionProperties())
        session = SessionStub([ResponseStub(200, {"ok": True})])
        transport = MaxApiTransport(
            base_url="https://platform-api.max.ru",
            headers={"Authorization": "token"},
            config=config,
            session=session,
        )

        result = await transport.request(method="GET", path="/me", model=DummyModel)

        self.assertEqual(result.status, 200)
        self.assertEqual(result.raw["ok"], True)
        self.assertEqual(result.parsed.payload["ok"], True)
        self.assertEqual(session.calls, 1)

    async def test_decode_error_on_invalid_json_content_type(self):
        config = TransportConfig.from_default_connection(DefaultConnectionProperties())
        session = SessionStub(
            [ResponseStub(200, "not-json", headers={"Content-Type": "application/json"})]
        )
        transport = MaxApiTransport(
            base_url="https://platform-api.max.ru",
            headers={"Authorization": "token"},
            config=config,
            session=session,
        )

        with self.assertRaises(ResponseDecodeError):
            await transport.request(method="GET", path="/me")


if __name__ == "__main__":
    unittest.main()
