import json
from pathlib import Path


def test_phase13_manifest_and_share_target():
    manifest = json.loads(Path('../frontend/public/manifest.webmanifest').read_text())
    assert manifest['display'] == 'standalone'
    assert manifest['share_target']['action'] == '/share'
    assert manifest['share_target']['params']['url'] == 'url'
    for icon in manifest['icons']:
        assert Path('../frontend/public', icon['src'].lstrip('/')).exists()


def test_phase13_service_worker_cache_version():
    sw = Path('../frontend/public/sw.js').read_text()
    assert 'ideaos-shell-v13' in sw
    assert '/manifest.webmanifest' in sw
    assert '/favicon.svg' in sw


def test_phase13_root_reports_phase():
    from app.main import APP_VERSION
    from app.config import APP_VERSION as CONFIG_VERSION
    assert APP_VERSION == CONFIG_VERSION
    assert APP_VERSION.startswith('0.14.0-phase14')
