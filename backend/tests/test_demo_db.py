from pathlib import Path

from frame_trace.config import Settings
from frame_trace.demo import seed_demo
from frame_trace.persistence import Database
from frame_trace.services import FrameTraceService


def make_service(tmp_path: Path):
    settings = Settings(data_dir=tmp_path/'data', database_path=tmp_path/'data'/'db.sqlite3', model_dir=tmp_path/'models', demo_dir=tmp_path/'demo')
    db = Database(settings.database_path)
    return FrameTraceService(db, settings)


def test_demo_seeds_personas_assets_and_review(tmp_path: Path):
    service = make_service(tmp_path)
    summary = service.seed_demo()
    assert summary['personas'] == 6
    assert len(service.list_personas()) == 6
    assert len(service.list_assets()) == 20
    assert len(service.review_queue()) == 2


def test_review_decision_is_auditable(tmp_path: Path):
    service = make_service(tmp_path); service.seed_demo()
    item = service.review_queue()[0]
    result = service.decide_review(item['detection_id'], 'different')
    assert result['decision'] == 'different'
    row = service.db.one('SELECT * FROM memberships WHERE detection_id=?',(item['detection_id'],))
    assert row['state']=='unassigned' and row['method']=='human'
    decision = service.db.one('SELECT * FROM review_decisions WHERE detection_id=?',(item['detection_id'],))
    assert decision['decision']=='different'


def test_persona_graph_contains_provenance_edges(tmp_path: Path):
    service = make_service(tmp_path); service.seed_demo()
    payload = service.graph.persona_graph('P001')
    edge_types = {edge.type for edge in payload.edges}
    assert 'appears_in' in edge_types
    assert 'published_by' in edge_types
    assert 'co_occurs_with' in edge_types
