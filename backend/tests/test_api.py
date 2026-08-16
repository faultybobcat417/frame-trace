from pathlib import Path

from fastapi.testclient import TestClient

from frame_trace.api import create_app
from frame_trace.config import Settings


def client_for(tmp_path: Path):
    settings = Settings(data_dir=tmp_path/'data', database_path=tmp_path/'data'/'db.sqlite3', model_dir=tmp_path/'models', demo_dir=tmp_path/'demo')
    app = create_app(settings)
    app.state.service.seed_demo()
    return TestClient(app)


def test_health_and_persona_flow(tmp_path: Path):
    client = client_for(tmp_path)
    assert client.get('/health').json()['status']=='ok'
    personas = client.get('/api/personas').json()
    assert len(personas)==6
    detail = client.get('/api/personas/P001').json()
    assert detail['id']=='P001' and detail['appearances']
    graph = client.get('/api/graph/persona/P001').json()
    assert graph['nodes'] and graph['edges']


def test_review_api(tmp_path: Path):
    client = client_for(tmp_path)
    item = client.get('/api/review').json()[0]
    response = client.post(f"/api/review/{item['detection_id']}/decision", json={'decision':'same'})
    assert response.status_code == 200
    assert response.json()['decision']=='same'


def test_import_status(tmp_path: Path):
    client = client_for(tmp_path)
    run = client.post('/api/import', json={'path':'~/authorized'}).json()
    assert run['stage']=='DISCOVER'
    status = client.get(f"/api/import/{run['id']}")
    assert status.status_code == 200
