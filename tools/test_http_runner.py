import unittest
import httpx
from http_runner import HttpRunner, RunnerError

class RunnerTests(unittest.TestCase):
    def run_status(self, status, expected=403):
        def handler(request):
            if request.url.port == 8081:
                return httpx.Response(200, json={"access_token": "test-secret"})
            self.assertEqual(request.headers["Authorization"], "Bearer test-secret")
            self.assertEqual(request.method, "GET")
            return httpx.Response(status, text="test-secret")
        with HttpRunner(httpx.MockTransport(handler)) as runner:
            runner.authenticate()
            result = runner.execute("lab-01-unregistered-read", expected)
        self.assertNotIn("test-secret", repr(result))
        return result

    def test_statuses(self):
        for status, outcome in [(403,"pass"), (200,"fail"), (401,"error"), (503,"error")]:
            with self.subTest(status=status):
                self.assertEqual(self.run_status(status).outcome, outcome)

    def test_unknown_action(self):
        with HttpRunner(httpx.MockTransport(lambda r: self.fail("unexpected request"))) as runner:
            self.assertEqual(runner.execute("unknown", 403).outcome, "error")

    def test_timeout(self):
        def handler(request):
            if request.url.port == 8081:
                return httpx.Response(200, json={"access_token":"secret"})
            raise httpx.ReadTimeout("secret", request=request)
        with HttpRunner(httpx.MockTransport(handler)) as runner:
            runner.authenticate()
            result = runner.execute("lab-01-active-read", 200)
            self.assertEqual(result.reason, "HTTP timeout")
            self.assertIsNone(result.actual)

    def test_bad_token(self):
        with HttpRunner(httpx.MockTransport(lambda r: httpx.Response(401))) as runner:
            with self.assertRaises(RunnerError):
                runner.authenticate()

if __name__ == "__main__":
    unittest.main()
