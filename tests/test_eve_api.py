import json
import unittest

from ccna_lab_builder.core.eve_api import EVEApi


class FakeResponse:
    ok = True
    status_code = 200
    text = '{"status":"success"}'

    def json(self):
        return {"status": "success", "code": 200, "message": "User logged in"}


class FakeSession:
    def __init__(self):
        self.last_url = None
        self.last_kwargs = None

    def post(self, url, **kwargs):
        self.last_url = url
        self.last_kwargs = kwargs
        return FakeResponse()


class EVEApiLoginTests(unittest.TestCase):
    def test_community_login_payload(self):
        api = EVEApi("eve.local", "admin", "secret", https=False)
        api.session = FakeSession()
        api.login()
        payload = json.loads(api.session.last_kwargs["data"])
        self.assertEqual(payload, {"username": "admin", "password": "secret"})
        self.assertEqual(api.session.last_url, "http://eve.local/api/auth/login")

    def test_pro_login_adds_html5(self):
        api = EVEApi("eve.local", "admin", "secret", https=True)
        api.session = FakeSession()
        api.login()
        payload = json.loads(api.session.last_kwargs["data"])
        self.assertEqual(payload["html5"], "0")
        self.assertEqual(api.session.last_url, "https://eve.local/api/auth/login")


if __name__ == "__main__":
    unittest.main()
