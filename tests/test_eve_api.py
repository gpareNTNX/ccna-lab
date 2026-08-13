import json
import unittest

from ccna_lab_builder.core.eve_api import EVEApi


class FakeResponse:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data or {"status": "success", "code": 200}
        self.ok = 200 <= status_code < 400
        self.text = json.dumps(self._data)

    def json(self):
        return self._data


class FakeSession:
    def __init__(self, request_responses=None):
        self.last_url = None
        self.last_kwargs = None
        self.login_count = 0
        self.request_count = 0
        self.requests = []
        self.request_responses = list(request_responses or [])

    def post(self, url, **kwargs):
        self.last_url = url
        self.last_kwargs = kwargs
        self.login_count += 1
        return FakeResponse(
            200,
            {"status": "success", "code": 200, "message": "User logged in"},
        )

    def request(self, method, url, **kwargs):
        self.request_count += 1
        self.requests.append((method, url, kwargs))
        if self.request_responses:
            return self.request_responses.pop(0)
        return FakeResponse()


class EVEApiLoginTests(unittest.TestCase):
    def test_community_login_payload(self):
        api = EVEApi("eve.local", "admin", "secret", https=False)
        api.session = FakeSession()
        api.login()
        payload = json.loads(api.session.last_kwargs["data"])
        self.assertEqual(payload, {"username": "admin", "password": "secret"})
        self.assertEqual(api.session.last_url, "http://eve.local/api/auth/login")
        self.assertEqual(
            api.session.last_kwargs["headers"]["Content-Type"],
            "application/json",
        )

    def test_pro_login_adds_html5(self):
        api = EVEApi("eve.local", "admin", "secret", https=True)
        api.session = FakeSession()
        api.login()
        payload = json.loads(api.session.last_kwargs["data"])
        self.assertEqual(payload["html5"], "0")
        self.assertEqual(api.session.last_url, "https://eve.local/api/auth/login")

    def test_412_session_timeout_reauthenticates_once(self):
        expired = FakeResponse(
            412,
            {
                "code": 412,
                "status": "unauthorized",
                "message": "User is not authenticated or session timed out (90001).",
            },
        )
        success = FakeResponse(
            200,
            {"code": 200, "status": "success", "message": "Lab has been created"},
        )
        api = EVEApi("eve.local", "admin", "secret")
        api.session = FakeSession([expired, success])

        result = api.request("POST", "/labs", json={"path": "/", "name": "Lab"})

        self.assertEqual(result["status"], "success")
        self.assertEqual(api.session.login_count, 1)
        self.assertEqual(api.session.request_count, 2)

    def test_failed_retry_does_not_loop_forever(self):
        expired1 = FakeResponse(
            412,
            {"code": 412, "status": "unauthorized", "message": "90001"},
        )
        expired2 = FakeResponse(
            412,
            {"code": 412, "status": "unauthorized", "message": "90001"},
        )
        api = EVEApi("eve.local", "admin", "secret")
        api.session = FakeSession([expired1, expired2])

        with self.assertRaises(RuntimeError):
            api.request("GET", "/auth")

        self.assertEqual(api.session.login_count, 1)
        self.assertEqual(api.session.request_count, 2)

    def test_ensure_folder_creates_missing_path_recursively(self):
        missing_parent = FakeResponse(
            404,
            {"code": 404, "status": "fail", "message": "Requested folder does not exist (60008)."},
        )
        created_parent = FakeResponse(
            200,
            {"code": 200, "status": "success", "message": "Folder has been created (60014)."},
        )
        missing_child = FakeResponse(
            404,
            {"code": 404, "status": "fail", "message": "Requested folder does not exist (60008)."},
        )
        created_child = FakeResponse(
            200,
            {"code": 200, "status": "success", "message": "Folder has been created (60014)."},
        )

        api = EVEApi("eve.local", "admin", "secret")
        api.session = FakeSession(
            [missing_parent, created_parent, missing_child, created_child]
        )

        result = api.ensure_folder("/CCNA-200-301/Scenarios")

        self.assertEqual(result, "/CCNA-200-301/Scenarios")
        self.assertEqual(api.session.request_count, 4)
        self.assertEqual(api.session.requests[1][0], "POST")
        self.assertEqual(
            api.session.requests[1][2]["json"],
            {"path": "/", "name": "CCNA-200-301"},
        )
        self.assertEqual(
            api.session.requests[3][2]["json"],
            {"path": "/CCNA-200-301", "name": "Scenarios"},
        )


if __name__ == "__main__":
    unittest.main()
