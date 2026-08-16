from pathlib import Path

import pytest

from frame_trace.cv import SFaceEmbedder, YuNetFaceDetector


def test_missing_model_paths_fail_closed(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        YuNetFaceDetector(tmp_path/'missing.onnx')
    with pytest.raises(FileNotFoundError):
        SFaceEmbedder(tmp_path/'missing2.onnx')
