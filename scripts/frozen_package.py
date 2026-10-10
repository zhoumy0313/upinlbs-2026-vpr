"""Scientific identity and human-confirmation checks for final evaluation."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()


def validate_package(path,require_confirmation=True):
    path=Path(path)
    package=json.loads(path.read_text())
    if package["final_test_seen_before_freeze"]:
        raise ValueError("This package is not a prospective freeze")
    if require_confirmation:
        approval=path.parent/"human_confirmation.json"
        if not approval.exists():raise ValueError("Final evaluation awaits human confirmation of this exact freeze package")
        evidence=json.loads(approval.read_text())
        if evidence.get("package_sha256")!=digest(path) or evidence.get("user_confirmed") is not True or not evidence.get("user_message_quote"):
            raise ValueError("Confirmation is missing or refers to another package")
    for name,value in package["code_config_sha256"].items():
        if digest(ROOT/name)!=value:raise ValueError("Frozen code/config changed: "+name)
    for name,entry in package["files"].items():
        if digest(path.parent/entry["path"])!=entry["sha256"]:raise ValueError("Frozen artifact changed: "+name)
    return package
