import json
from pathlib import Path

import pytest

from frame_trace.ingest import FolderAdapter, ManifestPackageAdapter, safe_child, sha256_file


def test_folder_adapter_discovers_supported_media(tmp_path: Path):
    (tmp_path/'a.jpg').write_bytes(b'jpg')
    (tmp_path/'b.mp4').write_bytes(b'mp4')
    (tmp_path/'ignore.txt').write_text('x')
    items = FolderAdapter().discover(tmp_path)
    assert [i.kind for i in items] == ['image','video']


def test_manifest_blocks_path_traversal(tmp_path: Path):
    with pytest.raises(ValueError):
        safe_child(tmp_path, '../escape.jpg')


def test_manifest_package(tmp_path: Path):
    media = tmp_path/'media'; media.mkdir()
    (media/'a.jpg').write_bytes(b'jpg')
    (tmp_path/'manifest.json').write_text(json.dumps({
        'source_id':'S1','source_name':'Demo','assets':[{'path':'media/a.jpg'}]
    }))
    items = ManifestPackageAdapter().discover(tmp_path)
    assert len(items)==1 and items[0].source_id=='S1'
    assert len(sha256_file(media/'a.jpg')) == 64
