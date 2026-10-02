from bridge_client import BridgeReply

def test_verified_read_only_payload_contains_process_and_records():
    reply=BridgeReply(True,'request',{'table_verified':True,'process_id':1234,'records':{'1000':{'active':False},'1002':{'value':'42'}}})
    assert reply.ok and reply.payload['table_verified']
    assert reply.payload['process_id']==1234
    assert reply.payload['records']['1002']['value']=='42'

def test_failed_sync_is_not_treated_as_verified():
    reply=BridgeReply(False,'request',{},'bridge timeout')
    assert not reply.ok
