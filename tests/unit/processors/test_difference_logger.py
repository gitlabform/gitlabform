import io
import logging
import textwrap

from rich.console import Console
from rich.logging import RichHandler

from gitlabform.constants import DIFF_LOG_LEVEL
from gitlabform.processors.util.difference_logger import DifferenceLogger


def test_empty_dict_current():
    current_config = dict()
    config_to_apply = {
        "foo": 123,
        "bar": "whatever",
    }
    result = DifferenceLogger.log_diff("test", current_config, config_to_apply, False, None, True)
    # the whitespace after "123" below is required!
    expected = textwrap.dedent("""
        test:
        foo: "???" => 123       
        bar: "???" => "whatever"
    """).strip()
    assert result == expected


def test_none_current():
    current_config = None
    config_to_apply = {
        "foo": 123,
        "bar": "whatever",
    }
    result = DifferenceLogger.log_diff("test", current_config, config_to_apply, False, None, True)
    # the whitespace after "123" below is required!
    expected = textwrap.dedent("""
        test:
        foo: "???" => 123       
        bar: "???" => "whatever"
    """).strip()
    assert result == expected


def test_diff_from_current():
    current_config = {
        "foo": 456,
        "bar": "whatever",
    }
    config_to_apply = {
        "foo": 123,
        "bar": "whatever",
    }
    result = DifferenceLogger.log_diff("test", current_config, config_to_apply, True, None, True)
    # the whitespace after "123" below is required!
    expected = textwrap.dedent("""
        test:
        foo: 456 => 123       
    """).strip()
    assert result == expected


def test_diff_output_no_changes():
    current_config = {
        "foo": 123,
        "bar": "whatever",
    }
    config_to_apply = {
        "foo": 123,
        "bar": "whatever",
    }
    result = DifferenceLogger.log_diff("test", current_config, config_to_apply, True, None, True)

    expected = textwrap.dedent("""

    """).strip()
    assert result == expected


def test_emits_diff_log_when_not_in_test_mode(caplog):
    """Verify that when called with `test=False`, a DIFF-level log is emitted
    and its message equals the returned diff text.

    Uses the `caplog` fixture to capture logs for the `gitlabform` logger.
    """

    current_config = {"foo": 1}
    config_to_apply = {"foo": 2}

    caplog.set_level(DIFF_LOG_LEVEL, logger="gitlabform")
    result = DifferenceLogger.log_diff("test", current_config, config_to_apply, False, None, False)

    assert any(r.levelno == DIFF_LOG_LEVEL and r.getMessage() == result for r in caplog.records)


def test_diff_logging_does_not_require_verbose_mode(caplog):
    """Ensure DIFF-level logs are emitted even when the logger is at WARNING
    (non-verbose) level, while INFO-level messages are suppressed.
    """

    pkg_logger = logging.getLogger("gitlabform")

    # Simulate application not in verbose mode: only WARNING and above should be emitted
    pkg_logger.setLevel(logging.WARNING)
    caplog.set_level(logging.WARNING, logger="gitlabform")

    # Emit an INFO message that should be suppressed
    pkg_logger.info("this is informational and should not appear")

    # Now emit a DIFF via the DifferenceLogger
    current_config = {"foo": 1}
    config_to_apply = {"foo": 2}
    result = DifferenceLogger.log_diff("test", current_config, config_to_apply, False, None, False)

    # INFO should not be present
    assert not any(r.levelno == logging.INFO for r in caplog.records)

    # DIFF should be present and equal to returned text
    assert any(r.levelno == DIFF_LOG_LEVEL and r.getMessage() == result for r in caplog.records)


def test_diff_logging_disables_rich_markup_for_bracketed_values():
    """Bracket-heavy diff payloads must not be parsed as Rich markup.

    Rich treats square-bracketed strings as markup when markup is enabled, so the
    diff log must explicitly disable it to preserve the literal text.
    """

    pkg_logger = logging.getLogger("gitlabform")
    original_handlers = list(pkg_logger.handlers)
    original_level = pkg_logger.level
    stream = io.StringIO()
    fmt_handler = RichHandler(markup=True, console=Console(file=stream, force_terminal=False, color_system=None))
    pkg_logger.handlers = [fmt_handler]
    pkg_logger.setLevel(DIFF_LOG_LEVEL)

    try:
        current_config = {"foo": "[before]"}
        config_to_apply = {"foo": "[after]"}
        DifferenceLogger.log_diff("test", current_config, config_to_apply, False, None, False)
    finally:
        pkg_logger.handlers = original_handlers
        pkg_logger.setLevel(original_level)

    output = stream.getvalue()
    assert "[before]" in output
    assert "[after]" in output
