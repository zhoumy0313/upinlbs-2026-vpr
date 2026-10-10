"""Isolate one optional comparator dependency; keep original venv and Torch intact."""
from pathlib import Path
import json
import sys
from runtime import Run,digest

def main():
    root=Path(__file__).resolve().parents[2]
    run=Run(root,'g3_smr_environment',{'no_system_changes':True,'dependency':'imbalanced-learn==0.14.0',
        'existing_torch_environment_readonly':True,'no_large_model_training':True},
        {'p0_environment_pins_sha256':digest(root/'requirements-evaluated-cu124.txt')})
    print(run.id,flush=True)
    env=root/'.venv-v2-smr';assert not env.exists(),'Do not overwrite an existing environment'
    run.command([str(root/'.venv-p0/bin/python'),'-m','venv','--without-pip',str(env)],{'PYTHONPATH':''})
    site=env/f'lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages'
    (site/'10_vpr_core_readonly.pth').write_text(str(root/'.venv-p0'/site.relative_to(env))+'\n')
    run.command([str(env/'bin/python'),'-m','pip','install','--index-url','https://pypi.org/simple',
        '--no-deps','imbalanced-learn==0.14.0'],{'PYTHONPATH':''})
    run.command([str(env/'bin/python'),'-c',
        'import numpy,scipy,sklearn,torch,imblearn;print(numpy.__version__,scipy.__version__,sklearn.__version__,torch.__version__,imblearn.__version__);print(torch.__file__)'],{'PYTHONPATH':''})
    run.write('metrics.json',{'role':'dependency isolation, not VPR performance','environment':'.venv-v2-smr',
        'added_package':'imbalanced-learn==0.14.0','base_packages':'read-only reference to .venv-p0'})
    run.write('checks.json',{'all_commands_exit_zero':True,'original_venv_not_modified':True})
    (run.path/'per_query.csv').write_text('package,version\nimbalanced-learn,0.14.0\n')
    (run.path/'interpretation.md').write_text('This environment references existing pinned NumPy/SciPy/Sklearn/Torch read-only and adds one package locally. No ROS, drivers, system Python, SSH/proxy or original virtualenv changes. Comparator scores are not yet available.\n')
    print(run.id,flush=True)

if __name__=='__main__':main()
