from typing import Any

import pytest

from app.external.remnawave_api import RemnaWaveAPI, RemnaWaveAPIError


@pytest.mark.asyncio
async def test_nodes_realtime_usage_falls_back_to_legacy_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')
    calls: list[tuple[str, tuple[int, ...]]] = []

    async def fake_make_request(
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        quiet_statuses: tuple[int, ...] = (),
    ) -> dict[str, Any]:
        calls.append((endpoint, quiet_statuses))
        if endpoint == '/api/bandwidth-stats/nodes/realtime':
            raise RemnaWaveAPIError('Cannot GET /api/bandwidth-stats/nodes/realtime', status_code=404)
        return {'response': [{'nodeUuid': 'node-1', 'downloadBytes': 10}]}

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    result = await api.get_bandwidth_stats_nodes_realtime()

    assert result == [{'nodeUuid': 'node-1', 'downloadBytes': 10}]
    assert calls == [
        ('/api/bandwidth-stats/nodes/realtime', (404,)),
        ('/api/nodes/usage/realtime', (404,)),
    ]


@pytest.mark.asyncio
async def test_nodes_realtime_usage_returns_empty_list_when_endpoints_are_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = RemnaWaveAPI('https://panel.example', 'token')

    async def fake_make_request(
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        quiet_statuses: tuple[int, ...] = (),
    ) -> dict[str, Any]:
        raise RemnaWaveAPIError(f'Cannot GET {endpoint}', status_code=404)

    monkeypatch.setattr(api, '_make_request', fake_make_request)

    assert await api.get_bandwidth_stats_nodes_realtime() == []
