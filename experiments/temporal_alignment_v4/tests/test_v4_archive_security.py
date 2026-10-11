"""Synthetic tar path safety checks, not a successful TUM audit."""
import importlib.util,sys,tarfile
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit_data import safe_members
def member(name,kind=tarfile.REGTYPE):
    m=tarfile.TarInfo(name);m.type=kind;return m
def base():return [member('root/rgb.txt'),member('root/groundtruth.txt')]
def test_valid_root_regular_files():assert len(safe_members(base()+[member('root/rgb/1.png')],'root'))==3
@pytest.mark.parametrize('name,kind',[('/tmp/a',tarfile.REGTYPE),('root/../../a',tarfile.REGTYPE),('another/rgb/1.png',tarfile.REGTYPE),('root/link',tarfile.SYMTYPE),('root/hard',tarfile.LNKTYPE),('root/device',tarfile.CHRTYPE),('root\\outside',tarfile.REGTYPE)])
def test_reject_unsafe_member(name,kind):
    with pytest.raises(ValueError):safe_members(base()+[member(name,kind)],'root')
def test_reject_duplicate():
    with pytest.raises(ValueError):safe_members(base()+[member('root/rgb.txt')],'root')
def test_reject_no_groundtruth():
    with pytest.raises(ValueError):safe_members([member('root/rgb.txt')],'root')
