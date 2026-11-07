"""Enable HTTP metrics with ENABLE_METRICS=true (disabled by default)."""

import os
import sys
from pathlib import Path
from time import perf_counter


BUCKETS = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
HTTP_METHODS = {
    "GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "CONNECT", "TRACE"
}

bind = "0.0.0.0:5000"
workers = int(os.environ.get("WEB_CONCURRENCY", "1"))
threads = 2
timeout = 60
preload_app = False


def metrics_enabled():
    return os.environ.get("ENABLE_METRICS", "false").lower() in {"true", "t", "1", "on"}


def instrument_app(app):
    from flask import abort, g, request

    if "http_metrics" in app.extensions:
        return app.extensions["http_metrics"]

    @app.before_request
    def block_public_metrics():
        if request.path.rstrip("/") == "/metrics" or request.path.startswith("/metrics/"):
            abort(404)

    app.extensions["http_metrics"] = None
    if not metrics_enabled():
        return None

    # Multiprocess mode must be configured before importing the Prometheus client.
    from prometheus_client import CollectorRegistry, Histogram

    registry = CollectorRegistry()
    request_duration = Histogram(
        "uqmarks_http_request_duration_seconds",
        "Flask request duration through response creation (seconds).",
        ("route", "method", "status"),
        buckets=BUCKETS,
        registry=registry,
    )
    app.extensions["http_metrics"] = registry

    @app.before_request
    def begin_request():
        g.http_metrics_started = perf_counter()

    @app.after_request
    def observe_request(response):
        started = getattr(g, "http_metrics_started", None)
        if started is None:
            return response

        route = request.url_rule.rule if request.url_rule else "unmatched"
        method = request.method if request.method in HTTP_METHODS else "OTHER"
        request_duration.labels(route, method, str(response.status_code)).observe(
            perf_counter() - started
        )
        return response

    return registry


def when_ready(server):
    if not metrics_enabled():
        return

    from prometheus_client import CollectorRegistry, multiprocess, start_http_server

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    server.metrics_server, server.metrics_thread = start_http_server(
        9100,
        addr=os.environ.get("METRICS_BIND_HOST", "127.0.0.1"),
        registry=registry,
    )


def child_exit(server, worker):
    if not metrics_enabled():
        return

    from prometheus_client import multiprocess

    multiprocess.mark_process_dead(worker.pid)


def on_exit(server):
    if hasattr(server, "metrics_server"):
        server.metrics_server.shutdown()
        server.metrics_server.server_close()


def main():
    if metrics_enabled():
        metrics_directory = Path("/tmp/uqmarks-prometheus")
        metrics_directory.mkdir(mode=0o700, exist_ok=True)
        for metric_file in metrics_directory.glob("*.db"):
            metric_file.unlink()
        os.environ["PROMETHEUS_MULTIPROC_DIR"] = str(metrics_directory)

    command = ["gunicorn", "--config", "python:http_metrics", *sys.argv[1:], "app:app"]
    os.execvp("gunicorn", command)


if __name__ == "__main__":
    main()
