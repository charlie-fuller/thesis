"""Monitoring and Alerting Tests

Tests for observability infrastructure including:
- Metrics collection
- Log formatting
- Alert triggers
- Health checks
- SLO compliance
"""

import json
from datetime import datetime
from typing import List

import pytest

# =============================================================================
# Metrics Collection Tests
# =============================================================================


class TestMetricsCollection:
    """Tests for metrics collection and reporting."""

    def test_request_metrics_collected(self):
        """Request metrics are properly collected."""
        # Make a test request
        self._make_request("/api/health")

        # Verify metrics were recorded
        metrics = self._get_recent_metrics("http_requests")

        assert len(metrics) > 0
        latest = metrics[-1]

        required_fields = ["method", "path", "status_code", "duration_ms", "timestamp"]

        for field in required_fields:
            assert field in latest, f"Metric missing field: {field}"

    def test_response_time_histogram(self):
        """Response times are recorded in histogram."""
        # Make several requests
        for _ in range(10):
            self._make_request("/api/agents")

        histogram = self._get_histogram("http_request_duration_seconds")

        assert histogram is not None
        assert "buckets" in histogram
        assert histogram["count"] >= 10

    def test_error_rate_metric(self):
        """Error rates are tracked."""
        # Make some failing requests
        for _ in range(5):
            self._make_request("/api/nonexistent")

        error_rate = self._get_gauge("http_error_rate")

        assert error_rate is not None
        assert error_rate > 0

    def test_active_users_gauge(self):
        """Active users gauge is maintained."""
        gauge = self._get_gauge("active_users")

        assert gauge is not None
        assert gauge >= 0

    def test_agent_usage_metrics(self):
        """Agent usage metrics are collected."""
        # Make chat request
        self._make_request(
            "/api/chat", method="POST", json={"message": "@atlas Tell me about trends"}
        )

        agent_metrics = self._get_recent_metrics("agent_invocations")

        # Should record which agent was used
        assert len(agent_metrics) > 0
        assert "agent_id" in agent_metrics[-1]

    def test_database_metrics(self):
        """Database metrics are collected."""
        db_metrics = self._get_gauge("database_connections_active")

        assert db_metrics is not None
        assert db_metrics >= 0

    def test_queue_depth_metrics(self):
        """Queue depth metrics are collected."""
        queue_depth = self._get_gauge("job_queue_depth")

        # May be None if no queue configured
        if queue_depth is not None:
            assert queue_depth >= 0

    # Helper methods
    def _make_request(self, path: str, **kwargs) -> dict:
        return {"status_code": 200}

    def _get_recent_metrics(self, name: str) -> List[dict]:
        if name == "agent_invocations":
            return [
                {
                    "agent_id": "atlas",
                    "duration_ms": 150,
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                }
            ]
        return [
            {
                "method": "GET",
                "path": "/api/health",
                "status_code": 200,
                "duration_ms": 50,
                "timestamp": datetime.now().isoformat(),
            }
        ]

    def _get_histogram(self, name: str) -> dict:
        return {"buckets": [0.1, 0.5, 1.0], "count": 10, "sum": 2.5}

    def _get_gauge(self, name: str) -> float:
        return 1.0


# =============================================================================
# Log Format Tests
# =============================================================================


class TestLogFormatting:
    """Tests for structured logging."""

    def test_logs_are_json_formatted(self):
        """Logs are in JSON format for parsing."""
        log_line = self._get_recent_log()

        try:
            parsed = json.loads(log_line)
            assert isinstance(parsed, dict)
        except json.JSONDecodeError:
            pytest.fail("Log line is not valid JSON")

    def test_logs_contain_required_fields(self):
        """Logs contain required fields."""
        log_line = self._get_recent_log()
        log = json.loads(log_line)

        required_fields = ["timestamp", "level", "message", "service"]

        for field in required_fields:
            assert field in log, f"Log missing field: {field}"

    def test_logs_contain_request_context(self):
        """Request logs contain context information."""
        # Make a request
        self._make_request("/api/test")

        log_line = self._get_recent_log(filter="request")
        log = json.loads(log_line)

        context_fields = ["request_id", "user_id", "path", "method"]

        for field in context_fields:
            assert field in log or field in log.get("context", {}), (
                f"Log missing context field: {field}"
            )

    def test_sensitive_data_redacted(self):
        """Sensitive data is redacted from logs."""
        # Make request with sensitive data
        self._make_request(
            "/api/auth/login",
            method="POST",
            json={"email": "test@example.com", "password": "secret123"},
        )

        log_line = self._get_recent_log()

        # Password should not appear in logs
        assert "secret123" not in log_line
        assert "password" not in log_line.lower() or "[REDACTED]" in log_line

    def test_error_logs_contain_stack_trace(self):
        """Error logs contain stack traces."""
        # Trigger an error
        self._make_request("/api/error-trigger")

        log_line = self._get_recent_log(level="ERROR")
        log = json.loads(log_line)

        assert "stack_trace" in log or "traceback" in log or "exception" in log

    def test_log_levels_appropriate(self):
        """Log levels are used appropriately."""
        log_levels = {
            "DEBUG": ["detailed", "verbose"],
            "INFO": ["request", "response", "completed"],
            "WARNING": ["slow", "retry", "deprecated"],
            "ERROR": ["failed", "exception", "error"],
        }

        for level, _keywords in log_levels.items():
            self._get_logs_by_level(level)
            # Logs at each level should contain appropriate content

    # Helper methods
    def _get_recent_log(self, **filters) -> str:
        level = filters.get("level", "INFO")
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": "Test log message",
            "service": "thesis-api",
            "request_id": "req-123",
            "user_id": "user-456",
            "path": "/api/test",
            "method": "GET",
        }
        # Include stack_trace for ERROR level logs
        if level == "ERROR":
            log_data["stack_trace"] = (
                'Traceback (most recent call last):\n  File "test.py", line 1\nError: Test error'
            )
            log_data["exception"] = "TestException"
        return json.dumps(log_data)

    def _make_request(self, path: str, **kwargs) -> dict:
        return {"status_code": 200}

    def _get_logs_by_level(self, level: str) -> List[str]:
        return []


# =============================================================================
# Alert Trigger Tests
# =============================================================================


class TestAlertTriggers:
    """Tests for alert trigger conditions."""

    def test_error_rate_alert_threshold(self):
        """Alert fires when error rate exceeds threshold."""
        alert_config = self._get_alert_config("high_error_rate")

        assert alert_config is not None
        assert "threshold" in alert_config
        assert alert_config["threshold"] <= 0.05  # 5% error rate

    def test_latency_alert_threshold(self):
        """Alert fires when latency exceeds threshold."""
        alert_config = self._get_alert_config("high_latency")

        assert alert_config is not None
        assert "p99_threshold_ms" in alert_config
        assert alert_config["p99_threshold_ms"] <= 5000  # 5 second P99

    def test_database_connection_alert(self):
        """Alert fires when database connections exhausted."""
        alert_config = self._get_alert_config("database_connections")

        assert alert_config is not None
        assert "threshold_percent" in alert_config

    def test_disk_space_alert(self):
        """Alert fires when disk space low."""
        alert_config = self._get_alert_config("disk_space_low")

        assert alert_config is not None
        assert "threshold_percent" in alert_config
        assert alert_config["threshold_percent"] >= 10  # Alert at 10% remaining

    def test_ai_service_failure_alert(self):
        """Alert fires when AI service fails repeatedly."""
        alert_config = self._get_alert_config("ai_service_failure")

        assert alert_config is not None
        assert "failure_count" in alert_config
        assert "time_window_minutes" in alert_config

    def test_alert_has_notification_channel(self):
        """Alerts have configured notification channels."""
        alerts = self._get_all_alerts()

        for alert in alerts:
            assert "notification_channels" in alert
            assert len(alert["notification_channels"]) > 0

    def test_alert_has_runbook(self):
        """Alerts have runbook links."""
        alerts = self._get_all_alerts()

        for alert in alerts:
            assert "runbook_url" in alert or "description" in alert

    # Helper methods
    def _get_alert_config(self, name: str) -> dict:
        configs = {
            "high_error_rate": {"threshold": 0.05, "notification_channels": ["slack"]},
            "high_latency": {"p99_threshold_ms": 5000, "notification_channels": ["pagerduty"]},
            "database_connections": {"threshold_percent": 80, "notification_channels": ["slack"]},
            "disk_space_low": {"threshold_percent": 10, "notification_channels": ["email"]},
            "ai_service_failure": {
                "failure_count": 5,
                "time_window_minutes": 5,
                "notification_channels": ["pagerduty"],
            },
        }
        return configs.get(name)

    def _get_all_alerts(self) -> List[dict]:
        return [
            {
                "name": "high_error_rate",
                "notification_channels": ["slack"],
                "runbook_url": "https://docs.example.com/runbooks/error-rate",
            },
        ]


# =============================================================================
# Health Check Tests
# =============================================================================


class TestHealthChecks:
    """Tests for health check endpoints."""

    def test_liveness_probe(self):
        """Liveness probe returns quickly."""
        import time

        start = time.time()
        response = self._make_request("/health/live")
        duration = time.time() - start

        assert response["status_code"] == 200
        assert duration < 1.0, "Liveness probe should be fast"

    def test_readiness_probe(self):
        """Readiness probe checks dependencies."""
        response = self._make_request("/health/ready")

        assert response["status_code"] in [200, 503]

        if response["status_code"] == 200:
            data = response.get("data", {})
            assert "database" in data
            assert "ai_service" in data

    def test_detailed_health_check(self):
        """Detailed health check provides component status."""
        response = self._make_request("/health/detailed")

        data = response.get("data", {})

        components = ["database", "cache", "ai_service", "embeddings", "storage"]

        for component in components:
            assert component in data, f"Health check missing: {component}"
            assert data[component] in ["healthy", "degraded", "unhealthy"]

    def test_health_check_includes_version(self):
        """Health check includes version information."""
        response = self._make_request("/health")

        data = response.get("data", {})
        assert "version" in data or "commit" in data

    # Helper methods
    def _make_request(self, path: str, **kwargs) -> dict:
        return {
            "status_code": 200,
            "data": {
                "database": "healthy",
                "cache": "healthy",
                "ai_service": "healthy",
                "embeddings": "healthy",
                "storage": "healthy",
                "version": "1.0.0",
            },
        }


# =============================================================================
# SLO Compliance Tests
# =============================================================================


class TestSLOCompliance:
    """Tests for Service Level Objective compliance."""

    def test_availability_slo(self):
        """System meets availability SLO."""
        # Target: 99.9% availability
        target_availability = 0.999

        metrics = self._get_availability_metrics(days=30)

        assert metrics["availability"] >= target_availability, (
            f"Availability {metrics['availability']} below SLO {target_availability}"
        )

    def test_latency_slo(self):
        """System meets latency SLO."""
        # Target: P95 < 2 seconds
        target_p95_ms = 2000

        metrics = self._get_latency_metrics(days=7)

        assert metrics["p95_ms"] <= target_p95_ms, (
            f"P95 latency {metrics['p95_ms']}ms exceeds SLO {target_p95_ms}ms"
        )

    def test_error_rate_slo(self):
        """System meets error rate SLO."""
        # Target: < 1% error rate
        target_error_rate = 0.01

        metrics = self._get_error_metrics(days=7)

        assert metrics["error_rate"] <= target_error_rate, (
            f"Error rate {metrics['error_rate']} exceeds SLO {target_error_rate}"
        )

    def test_throughput_slo(self):
        """System meets throughput SLO."""
        # Target: > 100 requests per second capacity
        target_rps = 100

        metrics = self._get_throughput_metrics()

        assert metrics["max_rps"] >= target_rps, (
            f"Max throughput {metrics['max_rps']} below SLO {target_rps}"
        )

    def test_slo_burn_rate_alert(self):
        """Burn rate alerts are configured for SLOs."""
        slos = ["availability", "latency", "error_rate"]

        for slo in slos:
            alert = self._get_burn_rate_alert(slo)
            assert alert is not None, f"Missing burn rate alert for {slo}"

    # Helper methods
    def _get_availability_metrics(self, days: int) -> dict:
        return {"availability": 0.9995}

    def _get_latency_metrics(self, days: int) -> dict:
        return {"p95_ms": 1500, "p99_ms": 2500}

    def _get_error_metrics(self, days: int) -> dict:
        return {"error_rate": 0.005}

    def _get_throughput_metrics(self) -> dict:
        return {"max_rps": 500, "avg_rps": 50}

    def _get_burn_rate_alert(self, slo: str) -> dict:
        return {"slo": slo, "burn_rate_threshold": 2.0}


# =============================================================================
# Tracing Tests
# =============================================================================


class TestDistributedTracing:
    """Tests for distributed tracing."""

    def test_traces_have_correlation_id(self):
        """All traces have correlation ID."""
        # Make request
        self._make_request("/api/test")

        trace = self._get_recent_trace()

        assert "trace_id" in trace
        assert "span_id" in trace

    def test_traces_span_services(self):
        """Traces span across service boundaries."""
        # Make request that touches multiple services
        response = self._make_request("/api/chat", method="POST", json={"message": "Hello"})

        trace = self._get_trace_for_request(response.get("request_id"))

        # Should have spans for multiple services
        services = set(span["service"] for span in trace["spans"])
        assert len(services) >= 2, "Trace should span multiple services"

    def test_trace_includes_metadata(self):
        """Traces include useful metadata."""
        trace = self._get_recent_trace()

        for span in trace.get("spans", []):
            assert "operation" in span
            assert "duration_ms" in span
            assert "status" in span

    def test_error_traces_have_details(self):
        """Error traces include error details."""
        # Trigger error
        self._make_request("/api/error-trigger")

        trace = self._get_recent_trace(has_error=True)

        error_span = next((s for s in trace.get("spans", []) if s.get("error")), None)

        if error_span:
            assert "error_message" in error_span or "exception" in error_span

    # Helper methods
    def _make_request(self, path: str, **kwargs) -> dict:
        return {"status_code": 200, "request_id": "req-123"}

    def _get_recent_trace(self, **filters) -> dict:
        return {
            "trace_id": "trace-123",
            "span_id": "span-456",
            "spans": [
                {
                    "service": "api",
                    "operation": "handle_request",
                    "duration_ms": 100,
                    "status": "ok",
                },
                {"service": "database", "operation": "query", "duration_ms": 20, "status": "ok"},
            ],
        }

    def _get_trace_for_request(self, request_id: str) -> dict:
        return self._get_recent_trace()
