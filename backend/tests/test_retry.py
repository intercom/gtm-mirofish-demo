"""Tests for app.utils.retry — retry_with_backoff and RetryableAPIClient."""

import pytest
from unittest.mock import patch

from app.utils.retry import retry_with_backoff, RetryableAPIClient


class TestRetryWithBackoff:
    def test_succeeds_first_try(self):
        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def ok():
            return 42

        assert ok() == 42

    @patch("app.utils.retry.time.sleep")
    def test_retries_on_failure_then_succeeds(self, mock_sleep):
        call_count = 0

        @retry_with_backoff(max_retries=3, initial_delay=0.01, jitter=False)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("transient")
            return "ok"

        assert flaky() == "ok"
        assert call_count == 3
        assert mock_sleep.call_count == 2

    @patch("app.utils.retry.time.sleep")
    def test_raises_after_all_retries_exhausted(self, mock_sleep):
        @retry_with_backoff(max_retries=2, initial_delay=0.01, jitter=False)
        def always_fail():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            always_fail()

    @patch("app.utils.retry.time.sleep")
    def test_on_retry_callback_called(self, mock_sleep):
        callbacks = []

        @retry_with_backoff(
            max_retries=2,
            initial_delay=0.01,
            jitter=False,
            on_retry=lambda e, n: callbacks.append(n),
        )
        def fail_once():
            if len(callbacks) == 0:
                raise ValueError("first")
            return "ok"

        assert fail_once() == "ok"
        assert callbacks == [1]

    @patch("app.utils.retry.time.sleep")
    def test_only_catches_specified_exceptions(self, mock_sleep):
        @retry_with_backoff(max_retries=3, initial_delay=0.01, exceptions=(ValueError,))
        def raises_type_error():
            raise TypeError("wrong type")

        with pytest.raises(TypeError):
            raises_type_error()
        mock_sleep.assert_not_called()


class TestRetryableAPIClient:
    @patch("app.utils.retry.time.sleep")
    def test_call_with_retry_succeeds(self, mock_sleep):
        client = RetryableAPIClient(max_retries=3, initial_delay=0.01)
        result = client.call_with_retry(lambda: 99)
        assert result == 99

    @patch("app.utils.retry.time.sleep")
    def test_call_with_retry_retries_then_succeeds(self, mock_sleep):
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("down")
            return "up"

        client = RetryableAPIClient(max_retries=3, initial_delay=0.01)
        assert client.call_with_retry(flaky) == "up"
        assert call_count == 2

    @patch("app.utils.retry.time.sleep")
    def test_call_batch_with_retry(self, mock_sleep):
        def process(item):
            if item == "bad":
                raise ValueError("bad item")
            return item.upper()

        client = RetryableAPIClient(max_retries=1, initial_delay=0.01)
        results, failures = client.call_batch_with_retry(
            ["hello", "bad", "world"],
            process,
            continue_on_failure=True,
        )
        assert results == ["HELLO", "WORLD"]
        assert len(failures) == 1
        assert failures[0]["index"] == 1

    @patch("app.utils.retry.time.sleep")
    def test_call_batch_stops_on_failure_when_configured(self, mock_sleep):
        def process(item):
            if item == "bad":
                raise ValueError("bad")
            return item

        client = RetryableAPIClient(max_retries=1, initial_delay=0.01)
        with pytest.raises(ValueError, match="bad"):
            client.call_batch_with_retry(
                ["good", "bad", "never_reached"],
                process,
                continue_on_failure=False,
            )
