import json, tempfile, threading, time
from pathlib import Path
from bridge_client import BridgeClient
from trainer_table import inventory

TABLE = Path(__file__).parent.parent / 'Enshrouded_Master_Trainer.CT'

def test_session_bound_mock_handshake():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); client=BridgeClient(root)
        def server():
            while not (root/'request.json').exists(): time.sleep(.01)
            req=json.loads((root/'request.json').read_text())
            (root/'response.json').write_text(json.dumps({'protocol':1,'session':req['session'],'request_id':req['request_id'],'ok':True,'payload':{'bridge_version':'mock'}}))
        threading.Thread(target=server,daemon=True).start()
        reply=client.call('hello')
        assert reply.ok and reply.payload['bridge_version']=='mock'

def test_stale_session_is_rejected_until_timeout():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); client=BridgeClient(root)
        def stale():
            while not (root/'request.json').exists(): time.sleep(.01)
            req=json.loads((root/'request.json').read_text())
            (root/'response.json').write_text(json.dumps({'session':'old','request_id':req['request_id'],'ok':True}))
        threading.Thread(target=stale,daemon=True).start()
        reply=client.call('hello',timeout=.15)
        assert not reply.ok and 'timeout' in reply.error

def test_full_manifest_uses_literal_utf8_for_record_1000():
    records = inventory(TABLE)
    assert len(records) == 161
    first = next(record for record in records if record.record_id == '1000')
    assert '\U0001f9d9' in first.description
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); client=BridgeClient(root)
        captured={}
        def server():
            while not (root/'request.json').exists(): time.sleep(.01)
            raw=(root/'request.json').read_bytes(); captured['raw']=raw
            req=json.loads(raw.decode('utf-8'))
            (root/'response.json').write_text(json.dumps({'session':req['session'],'request_id':req['request_id'],'ok':True,'payload':{'table_verified':True}},ensure_ascii=False),encoding='utf-8')
        threading.Thread(target=server,daemon=True).start()
        manifest=[{'id':r.record_id,'description':r.description} for r in records]
        assert client.call('hello',{'expected_records':manifest}).ok
        assert b'\\ud' not in captured['raw'].lower()
        assert first.description.encode('utf-8') in captured['raw']
