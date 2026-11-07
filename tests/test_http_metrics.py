import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from flask import Flask
from prometheus_client import CollectorRegistry, generate_latest, multiprocess
from prometheus_client.parser import text_string_to_metric_families

from http_metrics import (
    BUCKETS,
    child_exit,
    instrument_app,
    main,
    metrics_enabled,
    when_ready,
)


def make_app():
    app = Flask(__name__)
    instrument_app(app)

    @app.get("/api/courses/<code>")
    def course(code):
        return "ok"

    @app.get("/failure")
    def failure():
        raise RuntimeError("test failure")

    @app.route("/<path:path>")
    def catch_all(path):
        return "SPA"

    return app


def samples(registry, name):
    return [
        sample
        for family in text_string_to_metric_families(generate_latest(registry).decode())
        for sample in family.samples
        if sample.name == name
    ]


class HttpMetricsTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {"ENABLE_METRICS": "true"})
        environment.start()
        self.addCleanup(environment.stop)

    def test_metrics_are_disabled_by_default(self):
        with patch.dict(os.environ):
            os.environ.pop("ENABLE_METRICS", None)
            self.assertFalse(metrics_enabled())

    def test_disabled_metrics_skip_instrumentation_and_exporter(self):
        with patch.dict(os.environ, {"ENABLE_METRICS": "off"}):
            app = make_app()
            client = app.test_client()
            self.assertIsNone(app.extensions["http_metrics"])
            self.assertEqual(client.get("/api/courses/CSSE1001").status_code, 200)
            self.assertEqual(client.get("/metrics").status_code, 404)
            after_request_hooks = app.after_request_funcs.get(None, [])
            self.assertNotIn("observe_request", [hook.__name__ for hook in after_request_hooks])
            server = Mock()
            when_ready(server)
            child_exit(server, Mock())
            self.assertEqual(server.mock_calls, [])

    def test_disabled_startup_skips_multiprocess_storage(self):
        with (
            patch.dict(os.environ, {"ENABLE_METRICS": "false"}),
            patch("http_metrics.Path") as directory,
            patch("http_metrics.os.execvp") as launch,
        ):
            main()
            directory.assert_not_called()
            launch.assert_called_once()

    def test_route_templates_and_no_sensitive_labels(self):
        app = make_app()
        client = app.test_client()
        client.get(
            "/api/courses/CSSE1001?secret=private",
            headers={"X-Request-ID": "sensitive"},
        )
        client.get("/api/courses/MATH1051")
        counts = samples(app.extensions["http_metrics"], "uqmarks_http_request_duration_seconds_count")
        self.assertEqual(len(counts), 1)
        self.assertEqual(counts[0].value, 2)
        self.assertEqual(
            counts[0].labels,
            {"route": "/api/courses/<code>", "method": "GET", "status": "200"},
        )
        output = generate_latest(app.extensions["http_metrics"]).decode()
        for secret in ("CSSE1001", "MATH1051", "private", "sensitive"):
            self.assertNotIn(secret, output)
        buckets = samples(
            app.extensions["http_metrics"], "uqmarks_http_request_duration_seconds_bucket"
        )
        self.assertEqual(len(buckets), len(BUCKETS) + 1)
        duration_sums = samples(
            app.extensions["http_metrics"], "uqmarks_http_request_duration_seconds_sum"
        )
        self.assertGreater(duration_sums[0].value, 0)

    def test_public_metrics_paths_never_reach_catch_all(self):
        client = make_app().test_client()
        paths = (
            "/metrics", "/metrics/", "/metrics/anything",
            "/%6detrics", "/metrics?format=prometheus",
        )
        for path in paths:
            for method in ("GET", "POST", "HEAD", "OPTIONS"):
                self.assertEqual(client.open(path, method=method).status_code, 404)

    def test_status_methods_and_unmatched_requests(self):
        app = make_app()
        app.logger.disabled = True
        client = app.test_client()
        client.get("/failure")
        client.post("/api/courses/CSSE1001")
        client.open("/random", method="CUSTOM")
        counts = samples(app.extensions["http_metrics"], "uqmarks_http_request_duration_seconds_count")
        methods_and_statuses = {
            (sample.labels["method"], sample.labels["status"]) for sample in counts
        }
        self.assertEqual(
            methods_and_statuses, {("GET", "500"), ("POST", "405"), ("OTHER", "405")}
        )
        self.assertIn("unmatched", {sample.labels["route"] for sample in counts})

    def test_dash_routes_are_automatically_instrumented(self):
        from dash import Dash, Input, Output, html

        app = make_app()
        dash = Dash(__name__, server=app, url_base_pathname="/dash/")
        dash.layout = html.Div([html.Button(id="button"), html.Div(id="result")])

        @dash.callback(Output("result", "children"), Input("button", "n_clicks"))
        def update(clicks):
            return "done"

        client = app.test_client()
        self.assertEqual(client.get("/dash/_dash-layout").status_code, 200)
        response = client.post("/dash/_dash-update-component", json={
            "output": "result.children",
            "outputs": {"id": "result", "property": "children"},
            "inputs": [{"id": "button", "property": "n_clicks", "value": 1}],
            "state": [],
            "changedPropIds": ["button.n_clicks"],
        })
        self.assertEqual(response.status_code, 200)
        counts = samples(app.extensions["http_metrics"], "uqmarks_http_request_duration_seconds_count")
        self.assertEqual(
            {sample.labels["route"] for sample in counts},
            {"/dash/_dash-layout", "/dash/_dash-update-component"},
        )

    def test_initialization_is_idempotent_and_apps_have_separate_registries(self):
        first, second = make_app(), make_app()
        self.assertIs(instrument_app(first), first.extensions["http_metrics"])
        self.assertIsNot(
            first.extensions["http_metrics"], second.extensions["http_metrics"]
        )

    def test_consolidated_startup_prepares_storage_before_prometheus_import(self):
        with tempfile.TemporaryDirectory() as directory:
            script = """
import os
from pathlib import Path
import sys
from unittest.mock import patch
import http_metrics
assert 'prometheus_client' not in sys.modules
directory = Path(os.environ['TEST_METRICS_DIRECTORY'])
(directory / 'histogram_old.db').touch()
(directory / 'keep.txt').touch()
with patch('http_metrics.Path', return_value=directory), patch('http_metrics.os.execvp') as launch:
    http_metrics.main()
    launch.assert_called_once_with('gunicorn', [
        'gunicorn', '--config', 'python:http_metrics', 'app:app'
    ])
assert os.environ['PROMETHEUS_MULTIPROC_DIR'] == str(directory)
assert not (directory / 'histogram_old.db').exists()
assert (directory / 'keep.txt').exists()
"""
            subprocess.run(
                [sys.executable, "-c", script],
                env={**os.environ, "TEST_METRICS_DIRECTORY": directory},
                check=True,
                capture_output=True,
                text=True,
            )

    def test_multiprocess_aggregation_survives_worker_exit_and_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {**os.environ, "PROMETHEUS_MULTIPROC_DIR": directory}
            worker = """
import os
from flask import Flask
from http_metrics import instrument_app
app = Flask(__name__)
instrument_app(app)
app.add_url_rule('/api/<code>', view_func=lambda code: 'ok')
app.test_client().get('/api/CSSE1001')
print(os.getpid())
"""
            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry, path=directory)
            for expected_count in (1, 2, 3):
                result = subprocess.run(
                    [sys.executable, "-c", worker],
                    env=env, check=True, capture_output=True, text=True,
                )
                multiprocess.mark_process_dead(int(result.stdout.strip()), path=directory)
                counts = samples(
                    registry, "uqmarks_http_request_duration_seconds_count"
                )
                self.assertEqual(len(counts), 1)
                self.assertEqual(counts[0].value, expected_count)
                self.assertEqual(counts[0].labels["route"], "/api/<code>")


if __name__ == "__main__":
    unittest.main()
