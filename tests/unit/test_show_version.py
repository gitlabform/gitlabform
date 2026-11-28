from io import StringIO

import pytest
from rich.console import Console

import gitlabform


@pytest.mark.parametrize("installed_version", ["6.3.2", "6.4.0rc1"], ids=["outdated", "pre-release"])
def test_show_version_displays_latest_stable_version(monkeypatch, installed_version):
    output = StringIO()
    monkeypatch.setattr(gitlabform, "console", Console(file=output, width=120, force_terminal=False))
    monkeypatch.setattr(gitlabform, "package_version", lambda _: installed_version)
    monkeypatch.setattr(gitlabform.luddite, "get_version_pypi", lambda _: "6.3.3")

    gitlabform.GitLabForm._show_version(skip_version_check=False)

    assert "(the latest stable is 6.3.3)" in output.getvalue()
