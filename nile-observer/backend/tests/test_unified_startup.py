from datetime import datetime, timezone

import httpx
import pytest

from app.connectors.base import Batch
from app.connectors.opensky import OpenSkyConnector
from app.connectors.unified_radar import UnifiedRadarConnector
from app.schemas import Area


async def test_opensky_accepts_real_schema_with_zero_speed_and_heading():
    now = int(datetime.now(timezone.utc).timestamp())
    state = ['abc123', 'TEST', 'Egypt', now, now, 31.341, 30.088, 0, True, 0, 0, 0, None, 0, None, False, 0]
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={'time': now, 'states': [state]}))
    async with httpx.AsyncClient(transport=transport) as client:
        batch = await OpenSkyConnector().poll(client, Area())
    assert len(batch.observations) == 1
    item = batch.observations[0]
    assert item.observed_at.tzinfo is not None
    assert item.speed_mps == item.heading_deg == item.altitude == 0
    assert item.measurement_method == 'third_party_reported_position'


async def test_unified_all_failures_are_not_reported_as_success(monkeypatch):
    connector = UnifiedRadarConnector()

    async def fail(*args):
        raise RuntimeError('Provider unavailable')

    for provider in (connector.opensky, connector.ais, connector.noaa):
        monkeypatch.setattr(provider, 'poll', fail)
    with pytest.raises(RuntimeError, match='All unified providers are unavailable'):
        await connector.poll(None, Area())


async def test_unified_partial_failure_is_visible(monkeypatch):
    connector = UnifiedRadarConnector()

    async def empty(*args):
        return Batch()

    async def fail(*args):
        raise RuntimeError('Unavailable')

    monkeypatch.setattr(connector.opensky, 'poll', empty)
    monkeypatch.setattr(connector.ais, 'poll', fail)
    monkeypatch.setattr(connector.noaa, 'poll', fail)
    batch = await connector.poll(None, Area())
    assert batch.details['sources_active'] == 1
    assert batch.details['provider_health']['aisdecoder']['status'] == 'unavailable'
    assert batch.details['update_frequency_seconds'] == 30


def test_health_identifies_new_application(client):
    result = client.get('/api/health').json()
    assert result['application'] == 'unified-free-radar'
    assert result['app_root'].endswith('nile-observer')
    source = next(row for row in client.get('/api/sources').json() if row['id'] == 'unified_radar')
    assert source['enabled']
    assert source['update_interval'] == 30
