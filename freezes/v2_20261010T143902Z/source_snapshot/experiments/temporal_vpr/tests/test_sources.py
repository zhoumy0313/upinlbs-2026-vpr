import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fetch_sources import TextParser

def test_primary_body_extraction_preserves_formula_text_without_scripts():
    p=TextParser();p.feed('<script>secretless noise</script><h2>Method</h2><p>Past L frames</p><math><annotation>T=sum(S)/L</annotation></math>')
    result=''.join(p.parts)
    assert 'noise' not in result
    assert 'Past L frames' in result and 'T=sum(S)/L' in result
