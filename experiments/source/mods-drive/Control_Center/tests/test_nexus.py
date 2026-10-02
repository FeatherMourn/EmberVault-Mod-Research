import unittest
from core.nexus import NexusClient, NexusError

class Response:
    status_code = 200; ok = True
    def json(self): return {"results": [{"name": "real response"}]}

class Session:
    def __init__(self): self.calls = []
    def get(self, url, headers, params, timeout):
        self.calls.append((url, headers, params, timeout)); return Response()

class NexusTests(unittest.TestCase):
    def test_disconnected_fails_closed(self):
        with self.assertRaises(NexusError): NexusClient(session=Session()).browse()
    def test_mocked_browse_uses_identifying_headers(self):
        session = Session(); client = NexusClient("test-key", session=session)
        self.assertEqual(client.browse()[0]["name"], "real response")
        self.assertEqual(session.calls[0][1]["Application-Name"], "Enshrouded Mod Hub")
        self.assertEqual(session.calls[0][1]["apikey"], "test-key")

if __name__ == "__main__": unittest.main()
