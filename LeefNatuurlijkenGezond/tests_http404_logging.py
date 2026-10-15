import json
import logging
from io import StringIO

from django.http import HttpResponse, HttpResponseNotFound
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import path

from .middleware import HEADER_LIMIT, Log404RequestsMiddleware, _referrer


def existing_page(request):
    return HttpResponse("Existing page")


def missing_page(request, exception):
    return HttpResponseNotFound("Missing page", headers={"X-Diagnostic-Test": "kept"})


urlpatterns = [path("existing/", existing_page)]
handler404 = missing_page


@override_settings(
    ROOT_URLCONF=__name__, DEBUG=False, LOG_404_REQUESTS=True,
    ALLOWED_HOSTS=["testserver"],
)
class Http404LoggingTests(SimpleTestCase):
    def test_existing_page_does_not_log(self):
        with self.assertNoLogs("http404", level="WARNING"):
            self.assertEqual(self.client.get("/existing/").status_code, 200)

    def test_missing_page_logs_once_without_private_request_data(self):
        with self.assertLogs("http404", level="WARNING") as captured:
            response = self.client.get(
                "/bestaat-niet/?email=private-email",
                HTTP_REFERER="https://example.com/koekenpannen/?secret=private-query#private-fragment",
                HTTP_USER_AGENT="Googlebot diagnostic",
                HTTP_AUTHORIZATION="Bearer private-authorization",
                HTTP_COOKIE="session=private-cookie",
                REMOTE_ADDR="192.0.2.123",
                HTTP_X_FORWARDED_FOR="198.51.100.123",
            )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, b"Missing page")
        self.assertEqual(response["X-Diagnostic-Test"], "kept")
        self.assertNotIn("Location", response)
        self.assertEqual(len(captured.records), 1)
        message = captured.records[0].getMessage()
        self.assertEqual(
            message,
            "HTTP404 method=GET path=/bestaat-niet/ "
            'referrer=https://example.com/koekenpannen/ user_agent="Googlebot diagnostic"',
        )
        for private in (
            "private-", "192.0.2.123", "198.51.100.123", "email=", "secret=",
        ):
            self.assertNotIn(private, message)
        self.assertIsNone(captured.records[0].exc_info)

    @override_settings(LOG_404_REQUESTS=False)
    def test_disabled_does_not_log(self):
        with self.assertNoLogs("http404", level="WARNING"):
            self.assertEqual(self.client.get("/bestaat-niet/").status_code, 404)

    def test_missing_headers_have_safe_defaults(self):
        with self.assertLogs("http404", level="WARNING") as captured:
            self.client.get("/wp-admin/")
        self.assertEqual(
            captured.records[0].getMessage(),
            'HTTP404 method=GET path=/wp-admin/ referrer=- user_agent="-"',
        )

    def test_post_body_is_not_logged(self):
        with self.assertLogs("http404", level="WARNING") as captured:
            self.client.post("/missing/", data={"password": "private-body"})
        self.assertEqual(len(captured.records), 1)
        message = captured.records[0].getMessage()
        self.assertIn("method=POST", message)
        self.assertNotIn("private-body", message)

    def test_headers_are_limited_and_cannot_add_log_lines(self):
        request = RequestFactory().get("/missing/")
        request.META.update({
            "HTTP_USER_AGENT": 'bot"\r\nHTTP404 forged=true\t' + "x" * 1000,
            "HTTP_REFERER": "https://example.com/" + "x" * 1000 + "?private-query#fragment",
        })
        with self.assertLogs("http404", level="WARNING") as captured:
            Log404RequestsMiddleware(lambda request: HttpResponseNotFound())(request)
        self.assertEqual(len(captured.records), 1)
        message = captured.records[0].getMessage()
        self.assertNotIn("\n", message)
        self.assertNotIn("\r", message)
        self.assertNotIn("\t", message)
        self.assertNotIn("private-query", message)
        agent = json.loads(message.split(" user_agent=", 1)[1])
        self.assertEqual(len(agent), HEADER_LIMIT)
        self.assertIn(r'bot\"\r\n', message)

    def test_path_control_characters_cannot_add_log_lines(self):
        request = RequestFactory().get("/missing%0Aforged%09field/?private-query")
        with self.assertLogs("http404", level="WARNING") as captured:
            Log404RequestsMiddleware(lambda request: HttpResponseNotFound())(request)
        message = captured.records[0].getMessage()
        self.assertIn(r"path=/missing\nforged\tfield/", message)
        self.assertNotIn("\n", message)
        self.assertNotIn("\t", message)
        self.assertNotIn("private-query", message)

    def test_response_object_is_unchanged(self):
        request = RequestFactory().get("/missing/")
        original = HttpResponseNotFound(b"Unmodified", headers={"X-Original": "yes"})
        with self.assertLogs("http404", level="WARNING"):
            actual = Log404RequestsMiddleware(lambda request: original)(request)
        self.assertIs(actual, original)

    def test_other_status_codes_do_not_log(self):
        for status in (200, 301, 403, 500):
            with self.subTest(status=status), self.assertNoLogs("http404", level="WARNING"):
                request = RequestFactory().get("/existing/")
                Log404RequestsMiddleware(
                    lambda request: HttpResponse(status=status)
                )(request)

    def test_referrer_validation_and_credentials(self):
        cases = (
            ("https://user:password@example.com/path/?secret=1#fragment", "https://example.com/path/"),
            ("/path/?secret=1#fragment", "/path/"),
            ("https://[invalid/?secret=1", "-"),
            ("javascript:alert(1)?secret=1", "-"),
            ("", "-"),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(_referrer(value), expected)
        self.assertEqual(len(_referrer("https://example.com/" + "x" * 1000)), HEADER_LIMIT)

    def test_warning_reaches_stdout_once_without_propagating(self):
        dedicated_logger = logging.getLogger("http404")
        self.assertFalse(dedicated_logger.propagate)
        self.assertEqual(dedicated_logger.level, logging.WARNING)
        self.assertEqual(len(dedicated_logger.handlers), 1)
        output = StringIO()
        handler = dedicated_logger.handlers[0]
        old_stream = handler.setStream(output)
        try:
            self.client.get("/missing/")
        finally:
            handler.setStream(old_stream)
        self.assertEqual(
            output.getvalue(),
            'HTTP404 method=GET path=/missing/ referrer=- user_agent="-"\n',
        )


class Http404EnvironmentTests(SimpleTestCase):
    def test_boolean_environment_setting_is_opt_in(self):
        # Run the real setting expression without reloading settings or touching
        # database configuration, dotenv files or the process environment.
        import ast
        from pathlib import Path
        from types import SimpleNamespace
        from . import settings as project_settings

        tree = ast.parse(Path(project_settings.__file__).read_text())
        assignment = next(
            node for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "LOG_404_REQUESTS"
                    for target in node.targets)
        )
        expression = compile(ast.Expression(assignment.value), "<LOG_404_REQUESTS>", "eval")
        for value in (None, "", "false", "0", "no", "off", "unexpected", "true", "1", "yes", "on", " TRUE ", "Yes"):
            with self.subTest(value=value):
                fake_os = SimpleNamespace(getenv=lambda key, default: default if value is None else value)
                expected = value is not None and value.strip().lower() in {"true", "1", "yes", "on"}
                self.assertEqual(eval(expression, {"os": fake_os}), expected)
