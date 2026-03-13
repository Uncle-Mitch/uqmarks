import importlib
import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock


class FakeQuery:
    def filter_by(self, **kwargs):
        return self

    def first(self):
        return None


class FakeSession:
    def query(self, model):
        return FakeQuery()

    def add(self, instance):
        return None

    def commit(self):
        return None

    def rollback(self):
        return None


class FakeDB:
    def __init__(self):
        self.session = FakeSession()
        self.Model = object

    def init_app(self, app):
        return None

    def Column(self, *args, **kwargs):
        return None

    def String(self, *args, **kwargs):
        return None

    def Integer(self, *args, **kwargs):
        return None

    def Text(self, *args, **kwargs):
        return None

    def Index(self, *args, **kwargs):
        return None


def load_app_module():
    if importlib.util.find_spec("flask") is None:
        raise unittest.SkipTest("flask is not installed in the active interpreter")

    project_root = Path(__file__).resolve().parents[1]
    app_path = project_root / "app.py"

    os.environ.setdefault("SECRET_KEY", "test-secret")
    os.environ.setdefault("DEBUG_MODE", "F")
    os.environ.setdefault("POSTGRES_USER", "user")
    os.environ.setdefault("POSTGRES_PASSWORD", "pass")
    os.environ.setdefault("POSTGRES_DB", "db")
    os.environ.setdefault("MANAGER_ID", "123")
    os.environ.setdefault("ERROR_LOG_LINK", "https://example.invalid/error")
    os.environ.setdefault("LOG_LINK", "https://example.invalid/log")

    fake_get_assessment = types.ModuleType("get_assessment")

    class CourseMissingError(Exception):
        pass

    class CourseNotFoundError(Exception):
        def __init__(self, message="Course not found"):
            super().__init__(message)
            self.message = message

    class WrongSemesterError(Exception):
        def __init__(self, message="Wrong semester"):
            super().__init__(message)
            self.message = message

    class IncorrectCourseProfileError(Exception):
        def __init__(self, course_code="", semester="", year="", message="Incorrect course profile"):
            super().__init__(message)
            self.message = message

    fake_get_assessment.CourseMissingError = CourseMissingError
    fake_get_assessment.CourseNotFoundError = CourseNotFoundError
    fake_get_assessment.WrongSemesterError = WrongSemesterError
    fake_get_assessment.IncorrectCourseProfileError = IncorrectCourseProfileError
    fake_get_assessment.get_assessments = lambda *args, **kwargs: []

    fake_log_events = types.ModuleType("log_events")
    fake_log_events.log_search = lambda *args, **kwargs: None
    fake_log_events.log_error = lambda *args, **kwargs: None

    fake_cache = types.ModuleType("flask_cache")

    class FakeCacheBackend:
        def init_app(self, app):
            return None

        def memoize(self, timeout=None):
            def decorator(func):
                return func

            return decorator

    fake_cache.cache = FakeCacheBackend()
    fake_cache.get_semester_list = lambda: {}
    fake_cache.get_cached_df = lambda: None
    fake_cache.get_announcement = lambda: ""
    fake_cache.init_cache = lambda app: None

    fake_dash_app = types.ModuleType("dash_app")

    class FakeDash:
        def index(self):
            return "dash"

    fake_dash_app.create_dash_app = lambda app: FakeDash()

    fake_db_connection = types.ModuleType("db_connection")
    fake_db_connection.db = FakeDB()

    class Course:
        pass

    class SearchLogs:
        pass

    fake_db_connection.Course = Course
    fake_db_connection.SearchLogs = SearchLogs
    fake_db_connection.create_database = lambda app: None
    fake_db_connection.run_startup_migrations = lambda app: None

    fake_cors = types.ModuleType("flask_cors")
    fake_cors.cross_origin = lambda *args, **kwargs: (lambda func: func)
    fake_cors.CORS = lambda app: None

    fake_limiter = types.ModuleType("flask_limiter")

    class Limiter:
        def __init__(self, *args, **kwargs):
            return None

        def limit(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    fake_limiter.Limiter = Limiter

    fake_limiter_util = types.ModuleType("flask_limiter.util")
    fake_limiter_util.get_remote_address = lambda: "127.0.0.1"

    fake_limiter_errors = types.ModuleType("flask_limiter.errors")

    class RateLimitExceeded(Exception):
        pass

    fake_limiter_errors.RateLimitExceeded = RateLimitExceeded

    fake_sqlalchemy = types.ModuleType("sqlalchemy")
    fake_sqlalchemy.exc = types.SimpleNamespace(IntegrityError=Exception)

    fake_dotenv = types.ModuleType("dotenv")
    fake_dotenv.load_dotenv = lambda: None

    for name in [
        "app",
        "get_assessment",
        "log_events",
        "flask_cache",
        "dash_app",
        "db_connection",
        "flask_cors",
        "flask_limiter",
        "flask_limiter.util",
        "flask_limiter.errors",
        "sqlalchemy",
        "dotenv",
    ]:
        sys.modules.pop(name, None)

    sys.modules["get_assessment"] = fake_get_assessment
    sys.modules["log_events"] = fake_log_events
    sys.modules["flask_cache"] = fake_cache
    sys.modules["dash_app"] = fake_dash_app
    sys.modules["db_connection"] = fake_db_connection
    sys.modules["flask_cors"] = fake_cors
    sys.modules["flask_limiter"] = fake_limiter
    sys.modules["flask_limiter.util"] = fake_limiter_util
    sys.modules["flask_limiter.errors"] = fake_limiter_errors
    sys.modules["sqlalchemy"] = fake_sqlalchemy
    sys.modules["dotenv"] = fake_dotenv

    spec = importlib.util.spec_from_file_location("app", app_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["app"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ApiFeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app_module = load_app_module()
        cls.app_module.app.testing = True

    def setUp(self):
        self.client = self.app_module.app.test_client()
        self.app_module.get_semester_list = lambda: {}
        self.app_module.get_announcement = lambda: ""
        self.app_module.get_course = Mock(return_value=[])
        self.app_module.log_search = Mock()
        self.app_module.log_error = Mock()
        self.app_module.course_exists_for_semester_id = Mock(return_value=False)

    def test_get_semesters_returns_formatted_options(self):
        self.app_module.get_semester_list = lambda: {
            "2026S1": "Semester 1 2026",
            "2025S3": "Summer Semester 2025-2026",
        }

        response = self.client.get("/api/semesters/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            [
                {"value": "2026S1", "label": "Semester 1 2026"},
                {"value": "2025S3", "label": "Summer Semester 2025-2026"},
            ],
        )

    def test_get_course_requires_course_code_and_semester(self):
        response = self.client.get("/api/getcourse/")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {"success": False, "error": "Missing course code or semester."},
        )

    def test_get_course_rejects_invalid_course_code(self):
        response = self.client.get("/api/getcourse/?courseCode=bad&semesterId=2026S1")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {"success": False, "error": "Invalid course code or semester"},
        )

    def test_get_course_rejects_invalid_course_profile_url(self):
        response = self.client.get(
            "/api/getcourse/?courseCode=CSSE1001&semesterId=2026S1&courseProfileUrl=https://example.com/course"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {
                "success": False,
                "error": "Invalid course profile URL",
                "showURLRequest": True,
            },
        )

    def test_get_course_returns_assessment_items_without_course_profile_url(self):
        self.app_module.get_course.return_value = [
            ("Assignment 1", 20),
            ("Final Exam", 60),
        ]

        response = self.client.get("/api/getcourse/?courseCode=csse1001&semesterId=2026S1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {
                "success": True,
                "courseCode": "CSSE1001",
                "semesterId": "2026S1",
                "assessmentItems": [
                    {"title": "Assignment 1", "weight": 20},
                    {"title": "Final Exam", "weight": 60},
                ],
            },
        )
        self.app_module.get_course.assert_called_once_with("CSSE1001", "1", "2026")
        self.app_module.log_search.assert_called_once()

    def test_get_course_uses_section_code_when_course_profile_url_is_supplied(self):
        self.app_module.get_course.return_value = [("Project", 40)]

        response = self.client.get(
            "/api/getcourse/?courseCode=CSSE1001&semesterId=2026S1&courseProfileUrl=https://course-profiles.uq.edu.au/course-profiles/CSSE1001-123-456#assessment"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["assessmentItems"], [{"title": "Project", "weight": 40}])
        self.app_module.get_course.assert_called_once_with(
            "CSSE1001", "1", "2026", section_code="CSSE1001-123-456"
        )

    def test_get_course_returns_404_when_course_is_missing(self):
        self.app_module.get_course.side_effect = self.app_module.CourseMissingError("missing")

        response = self.client.get("/api/getcourse/?courseCode=CSSE1001&semesterId=2026S1")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.get_json(),
            {"success": False, "error": "", "showURLRequest": True},
        )

    def test_get_course_returns_default_error_for_unexpected_exceptions(self):
        self.app_module.get_course.side_effect = RuntimeError("boom")

        response = self.client.get("/api/getcourse/?courseCode=CSSE1001&semesterId=2026S1")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {
                "success": False,
                "error": self.app_module.DEFAULT_INVALID_TEXT,
            },
        )
        self.app_module.log_error.assert_called_once()

    def test_get_announcement_returns_success_payload(self):
        self.app_module.get_announcement = lambda: "Maintenance tonight"

        response = self.client.get("/api/announcement/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"success": True, "announcement": "Maintenance tonight"},
        )

    def test_analytics_page_load_rejects_non_object_json_payload(self):
        response = self.client.post("/api/analytics/page-load/", json=[])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {"success": False, "error": "Invalid JSON payload."},
        )

    def test_analytics_page_load_rejects_non_list_entries(self):
        response = self.client.post("/api/analytics/page-load/", json={"entries": {}})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {"success": False, "error": "Invalid entries payload."},
        )

    def test_analytics_page_load_rejects_more_than_maximum_entries(self):
        response = self.client.post(
            "/api/analytics/page-load/",
            json={"entries": [{} for _ in range(26)]},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {"success": False, "error": "Maximum 25 entries per request."},
        )

    def test_analytics_page_load_logs_only_existing_courses(self):
        self.app_module.course_exists_for_semester_id = Mock(
            side_effect=lambda course_code, semester_id: (course_code, semester_id)
            in {("CSSE1001", "2026S1"), ("MATH1051", "2025S2")}
        )

        response = self.client.post(
            "/api/analytics/page-load/",
            json={
                "entries": [
                    {"courseCode": "csse1001", "semesterId": "2026S1"},
                    {"courseCode": "math1051", "semesterId": "2025S2"},
                    {"courseCode": "bad", "semesterId": "2026S1"},
                    {"courseCode": "csse1001", "semesterId": "not-a-semester"},
                    "skip-me",
                ]
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"success": True, "logged": 2})
        self.assertEqual(self.app_module.log_search.call_count, 2)
        self.app_module.log_search.assert_any_call(
            "CSSE1001",
            "1",
            "2026",
            self.app_module.THIS_FOLDER,
            self.app_module.app.config["ENABLE_LOGGING"],
            event_type="page_load",
        )
        self.app_module.log_search.assert_any_call(
            "MATH1051",
            "2",
            "2025",
            self.app_module.THIS_FOLDER,
            self.app_module.app.config["ENABLE_LOGGING"],
            event_type="page_load",
        )


class AppFunctionUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app_module = load_app_module()

    def setUp(self):
        self.original_proxy_url = self.app_module.COURSE_PROFILE_PROXY_URL
        self.app_module.requests.get = Mock()

    def tearDown(self):
        self.app_module.COURSE_PROFILE_PROXY_URL = self.original_proxy_url

    def test_is_valid_course_code_accepts_expected_format(self):
        self.assertTrue(self.app_module.is_valid_course_code("CSSE1001"))
        self.assertTrue(self.app_module.is_valid_course_code("math1051"))

    def test_is_valid_course_code_rejects_invalid_formats(self):
        self.assertFalse(self.app_module.is_valid_course_code("CSSE101"))
        self.assertFalse(self.app_module.is_valid_course_code("CSSE10012"))
        self.assertFalse(self.app_module.is_valid_course_code("12341001"))
        self.assertFalse(self.app_module.is_valid_course_code("CSSE-1001"))

    def test_is_valid_semester_id_accepts_supported_values(self):
        self.assertTrue(self.app_module.is_valid_semester_id("2026S1"))
        self.assertTrue(self.app_module.is_valid_semester_id("2025S2"))
        self.assertTrue(self.app_module.is_valid_semester_id("2024S3"))

    def test_is_valid_semester_id_rejects_invalid_formats(self):
        self.assertFalse(self.app_module.is_valid_semester_id("26S1"))
        self.assertFalse(self.app_module.is_valid_semester_id("2026S4"))
        self.assertFalse(self.app_module.is_valid_semester_id("2026T1"))
        self.assertFalse(self.app_module.is_valid_semester_id("semester-1"))

    def test_course_exists_for_semester_id_rejects_invalid_inputs_without_querying_db(self):
        query = Mock()
        self.app_module.db.session.query = query

        self.assertFalse(self.app_module.course_exists_for_semester_id("bad", "2026S1"))
        self.assertFalse(self.app_module.course_exists_for_semester_id("CSSE1001", "bad"))
        query.assert_not_called()

    def test_course_exists_for_semester_id_checks_database_for_valid_inputs(self):
        record = object()
        fake_query = Mock()
        fake_query.filter_by.return_value.first.return_value = record
        self.app_module.db.session.query = Mock(return_value=fake_query)

        result = self.app_module.course_exists_for_semester_id("CSSE1001", "2026S1")

        self.assertTrue(result)
        self.app_module.db.session.query.assert_called_once_with(self.app_module.Course)
        fake_query.filter_by.assert_called_once_with(code="CSSE1001", year=2026, semester=1)

    def test_is_valid_course_profile_url_accepts_normal_and_archive_urls(self):
        self.assertTrue(
            self.app_module.is_valid_course_profile_url(
                "https://course-profiles.uq.edu.au/course-profiles/CSSE1001-123-456"
            )
        )
        self.assertTrue(
            self.app_module.is_valid_course_profile_url(
                "https://course-profiles.uq.edu.au/course-profiles/CSSE1001-123-456#assessment-summary"
            )
        )
        self.assertTrue(
            self.app_module.is_valid_course_profile_url(
                "https://archive.course-profiles.uq.edu.au/student_section_loader/section_987/654"
            )
        )

    def test_is_valid_course_profile_url_rejects_unexpected_domains_and_formats(self):
        self.assertFalse(
            self.app_module.is_valid_course_profile_url(
                "https://example.com/course-profiles/CSSE1001-123-456"
            )
        )
        self.assertFalse(
            self.app_module.is_valid_course_profile_url(
                "https://course-profiles.uq.edu.au/course-profiles/CSSE1001"
            )
        )
        self.assertFalse(
            self.app_module.is_valid_course_profile_url(
                "http://course-profiles.uq.edu.au/course-profiles/CSSE1001-123-456"
            )
        )

    def test_get_section_code_from_normal_url_extracts_course_section_code(self):
        result = self.app_module.get_section_code_from_url(
            "https://course-profiles.uq.edu.au/course-profiles/CSSE1001-123-456#assessment",
            "CSSE1001",
            "1",
            "2026",
        )

        self.assertEqual(result, "CSSE1001-123-456")

    def test_get_section_code_from_archive_url_extracts_numeric_section_code(self):
        result = self.app_module.get_section_code_from_url(
            "https://archive.course-profiles.uq.edu.au/student_section_loader/section_999/654321",
            "CSSE1001",
            "1",
            "2026",
        )

        self.assertEqual(result, "654321")

    def test_get_section_code_from_url_raises_when_url_does_not_match_expected_pattern(self):
        with self.assertRaises(self.app_module.IncorrectCourseProfileError):
            self.app_module.get_section_code_from_url(
                "https://course-profiles.uq.edu.au/course-profiles/WRONG1001-123-456",
                "CSSE1001",
                "1",
                "2026",
            )

    def test_fetch_course_profile_url_from_proxy_returns_none_when_proxy_not_configured(self):
        self.app_module.COURSE_PROFILE_PROXY_URL = ""

        result = self.app_module.fetch_course_profile_url_from_proxy("CSSE1001", "1", "2026")

        self.assertIsNone(result)
        self.app_module.requests.get.assert_not_called()

    def test_fetch_course_profile_url_from_proxy_returns_valid_url_from_json_payload(self):
        self.app_module.COURSE_PROFILE_PROXY_URL = "https://proxy.example/api"
        response = Mock(status_code=200)
        response.json.return_value = {
            "courseProfileUrl": "https://course-profiles.uq.edu.au/course-profiles/CSSE1001-123-456"
        }
        self.app_module.requests.get.return_value = response

        result = self.app_module.fetch_course_profile_url_from_proxy("CSSE1001", "1", "2026")

        self.assertEqual(
            result,
            "https://course-profiles.uq.edu.au/course-profiles/CSSE1001-123-456",
        )
        self.app_module.requests.get.assert_called_once_with(
            "https://proxy.example/api",
            params={"courseCode": "CSSE1001", "semester": "2026S1"},
            timeout=10,
        )

    def test_fetch_course_profile_url_from_proxy_returns_none_for_invalid_payload_url(self):
        self.app_module.COURSE_PROFILE_PROXY_URL = "https://proxy.example/api"
        response = Mock(status_code=200)
        response.json.return_value = {"courseProfileUrl": "https://example.com/not-allowed"}
        self.app_module.requests.get.return_value = response

        result = self.app_module.fetch_course_profile_url_from_proxy("CSSE1001", "1", "2026")

        self.assertIsNone(result)

    def test_fetch_course_profile_url_from_proxy_returns_none_for_non_200_response(self):
        self.app_module.COURSE_PROFILE_PROXY_URL = "https://proxy.example/api"
        self.app_module.requests.get.return_value = Mock(status_code=503)

        result = self.app_module.fetch_course_profile_url_from_proxy("CSSE1001", "1", "2026")

        self.assertIsNone(result)

    def test_fetch_course_profile_url_from_proxy_returns_none_when_request_raises(self):
        self.app_module.COURSE_PROFILE_PROXY_URL = "https://proxy.example/api"
        self.app_module.requests.get.side_effect = RuntimeError("network error")

        result = self.app_module.fetch_course_profile_url_from_proxy("CSSE1001", "1", "2026")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
