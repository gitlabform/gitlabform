import io
import logging

import pytest
from rich.console import Console
from rich.logging import RichHandler

from gitlabform import GitLabForm
from gitlabform.constants import NOTICE_LOG_LEVEL


def test_show_summary_with_bracketed_error_text_is_logged_literally():
    """Failed group/project names may contain brackets, f.e. when they include
    exception text. Rich markup is enabled per record for these lines, so any
    interpolated value has to be escaped - otherwise Rich either swallows the
    bracketed text or raises a MarkupError from outside RichHandler.emit()'s
    try/except, aborting the run.
    """

    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_level = root_logger.level
    stream = io.StringIO()
    handler = RichHandler(console=Console(file=stream, width=200, force_terminal=False, color_system=None))
    root_logger.handlers = [handler]
    root_logger.setLevel(NOTICE_LOG_LEVEL)

    try:
        with pytest.raises(SystemExit):
            GitLabForm._show_summary([], [], 0, 0, {1: "KeyError [/oops] in [a-z]+"}, {})
    finally:
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)

    assert "KeyError [/oops] in [a-z]+" in stream.getvalue()
