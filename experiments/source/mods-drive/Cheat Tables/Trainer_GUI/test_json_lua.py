from pathlib import Path

def test_bundled_json_has_required_codec_surface():
    source = (Path(__file__).parent / 'json.lua').read_text(encoding='utf-8')
    assert 'M.encode=encode' in source
    assert 'M.decode=decode' in source
    assert 'M.null' in source
    assert 'invalid unicode escape' in source
