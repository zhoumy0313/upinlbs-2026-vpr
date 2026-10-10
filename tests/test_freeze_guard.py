"""Synthetic identity/confirmation checks; these do not run final VPR images."""
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/frozen_package.py"
spec=importlib.util.spec_from_file_location("frozen_package",SCRIPT)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_final_entry_rejects_missing_or_wrong_package_confirmation(tmp_path):
    path=tmp_path/"selection.json"
    path.write_text(json.dumps({"final_test_seen_before_freeze":False,"files":{},"code_config_sha256":{}}))
    with pytest.raises(ValueError,match="awaits human confirmation"):module.validate_package(path)
    (tmp_path/"human_confirmation.json").write_text(json.dumps({"package_sha256":"another-version","user_confirmed":True,"user_message_quote":"SYNTHETIC TEST ONLY"}))
    with pytest.raises(ValueError,match="another package"):module.validate_package(path)


def test_review_detects_modified_parameter_artifacts_without_final_images(tmp_path):
    artifact=tmp_path/"parameters.json";artifact.write_text('{"threshold":0.25}')
    path=tmp_path/"selection.json"
    path.write_text(json.dumps({"final_test_seen_before_freeze":False,"files":{"parameters":{"path":artifact.name,"sha256":module.digest(artifact)}},"code_config_sha256":{}}))
    module.validate_package(path,require_confirmation=False)
    artifact.write_text('{"threshold":0.75}')
    with pytest.raises(ValueError,match="artifact changed"):module.validate_package(path,require_confirmation=False)
