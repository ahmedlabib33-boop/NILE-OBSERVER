"""Report source states for this application without printing the access token."""
import sys
import httpx
from app.config import get_settings


def main():
    cfg = get_settings()
    token = cfg.app_api_key.get_secret_value()
    if not token:
        token = (cfg.data_dir / 'access-token').read_text().strip()
    with httpx.Client(base_url='http://127.0.0.1:8000', timeout=5, trust_env=False) as client:
        health = client.get('/api/health')
        health.raise_for_status()
        if health.json().get('application') != 'unified-free-radar':
            raise RuntimeError('Port 8000 is serving another application')
        response = client.get('/api/sources', headers={'Authorization': 'Bearer ' + token})
        response.raise_for_status()
        sources = response.json()
    print('Unified Free Radar: API healthy; frontend served at /#satellite')
    for source in sources:
        if source['enabled']:
            print(f"{source['id']}: {source['status']} | poll {source['update_interval']}s | last count {source['last_count']}")
            if source.get('error'):
                print('  ' + source['error'])
    return 0


if __name__ == '__main__':
    sys.exit(main())
