from unittest.mock import MagicMock

import pytest
from gitlab import GitlabGetError, GitlabListError

from gitlabform.processors.project.files_processor import FilesProcessor


def _make_branch(name: str, branch_id: str = "abc123"):
    branch = MagicMock()
    branch.name = name
    branch.get_id.return_value = branch_id
    return branch


class _ConfigDict(dict):
    """Minimal stand-in for Configuration that supports pipe-separated path lookups."""

    def get(self, key, default=None):
        if isinstance(key, str) and "|" in key:
            current = self
            for token in key.split("|"):
                if isinstance(current, dict) and token in current:
                    current = current[token]
                else:
                    return default
            return current
        return super().get(key, default)


class TestAppendBranchesMatchingRef:
    def setup_method(self):
        self.gitlab = MagicMock()
        self.config = MagicMock()
        self.processor = FilesProcessor(self.gitlab, self.config, strict=False)
        self.project = MagicMock()

    def test_wildcard_ref_converts_to_re2_regex(self):
        self.project.branches.list.return_value = []

        result: list = []
        self.processor.append_branches_matching_ref(result, "README.md", self.project, "bugfix/*")

        self.project.branches.list.assert_called_once_with(get_all=True, regex="^bugfix/.*$")

    def test_wildcard_ref_escapes_regex_metacharacters(self):
        self.project.branches.list.return_value = []

        result: list = []
        self.processor.append_branches_matching_ref(result, "README.md", self.project, "release-1.0*")

        _, kwargs = self.project.branches.list.call_args
        assert kwargs["regex"] == r"^release\-1\.0.*$"

    def test_wildcard_ref_sorts_branches_by_name(self):
        self.project.branches.list.return_value = [
            _make_branch("bugfix/zeta"),
            _make_branch("bugfix/alpha"),
            _make_branch("bugfix/mu"),
        ]

        result: list = []
        self.processor.append_branches_matching_ref(result, "README.md", self.project, "bugfix/*")

        assert [b.name for b in result] == ["bugfix/alpha", "bugfix/mu", "bugfix/zeta"]

    def test_wildcard_ref_skips_branches_without_id(self):
        self.project.branches.list.return_value = [
            _make_branch("bugfix/a", branch_id="id-a"),
            _make_branch("bugfix/b", branch_id=""),
            _make_branch("bugfix/c", branch_id=None),
        ]

        result: list = []
        self.processor.append_branches_matching_ref(result, "README.md", self.project, "bugfix/*")

        assert [b.name for b in result] == ["bugfix/a"]

    def test_wildcard_ref_list_error_non_strict_warns(self):
        self.project.branches.list.side_effect = GitlabListError("boom")

        result: list = []
        self.processor.append_branches_matching_ref(result, "README.md", self.project, "bugfix/*")

        assert result == []

    def test_wildcard_ref_list_error_strict_exits(self):
        self.processor.strict = True
        self.project.branches.list.side_effect = GitlabListError("boom")

        with pytest.raises(SystemExit):
            self.processor.append_branches_matching_ref([], "README.md", self.project, "bugfix/*")

    def test_literal_ref_calls_branches_get(self):
        branch = _make_branch("main")
        self.project.branches.get.return_value = branch

        result: list = []
        self.processor.append_branches_matching_ref(result, "README.md", self.project, "main")

        self.project.branches.get.assert_called_once_with("main")
        assert result == [branch]

    def test_literal_ref_get_error_non_strict_warns(self):
        self.project.branches.get.side_effect = GitlabGetError("not found")

        result: list = []
        self.processor.append_branches_matching_ref(result, "README.md", self.project, "missing")

        assert result == []

    def test_literal_ref_get_error_strict_exits(self):
        self.processor.strict = True
        self.project.branches.get.side_effect = GitlabGetError("not found")

        with pytest.raises(SystemExit):
            self.processor.append_branches_matching_ref([], "README.md", self.project, "missing")


class TestProcessConfigurationDispatch:
    def setup_method(self):
        self.gitlab = MagicMock()
        self.config = MagicMock()
        self.processor = FilesProcessor(self.gitlab, self.config, strict=False)

        # AbstractProcessor builds self.gl via GitlabWrapper in __init__; replace it
        self.processor.gl = MagicMock()
        self.project = MagicMock()
        self.processor.gl.get_project_by_path_cached.return_value = self.project

        # Stub out process_branch so we only test the dispatch
        self.processor.process_branch = MagicMock()

    def _config(self, branches, **extra):
        return _ConfigDict({"files": {"README.md": {"branches": branches, **extra}}})

    def test_all_uses_branches_list(self):
        all_branches = [_make_branch("main"), _make_branch("dev")]
        self.project.branches.list.return_value = all_branches

        self.processor._process_configuration("g/p", self._config("all"))

        self.project.branches.list.assert_called_once_with(get_all=True, lazy=True)
        assert self.processor.process_branch.call_count == 2

    def test_protected_expands_each_protected_branch(self):
        wildcard_rule = MagicMock()
        wildcard_rule.name = "bugfix/*"
        literal_rule = MagicMock()
        literal_rule.name = "main"
        self.project.protectedbranches.list.return_value = [wildcard_rule, literal_rule]

        # First call (wildcard): branches.list returns 2 matching branches
        # Second call (literal): branches.get returns main
        self.project.branches.list.return_value = [_make_branch("bugfix/a"), _make_branch("bugfix/b")]
        self.project.branches.get.return_value = _make_branch("main")

        self.processor._process_configuration("g/p", self._config("protected"))

        assert self.processor.process_branch.call_count == 3

    def test_list_calls_helper_per_entry(self):
        self.project.branches.get.return_value = _make_branch("main")
        self.project.branches.list.return_value = [_make_branch("bugfix/a")]

        self.processor._process_configuration("g/p", self._config(["main", "bugfix/*"]))

        self.project.branches.get.assert_called_once_with("main")
        self.project.branches.list.assert_called_once_with(get_all=True, regex="^bugfix/.*$")
        assert self.processor.process_branch.call_count == 2

    def test_only_first_branch_breaks_after_first(self):
        self.project.branches.list.return_value = [_make_branch("a"), _make_branch("b"), _make_branch("c")]

        cfg = self._config("all", only_first_branch=True)
        self.processor._process_configuration("g/p", cfg)

        assert self.processor.process_branch.call_count == 1

    def test_skip_short_circuits_file(self):
        self.project.branches.list.return_value = [_make_branch("main")]

        cfg = self._config("all", skip=True)
        self.processor._process_configuration("g/p", cfg)

        self.processor.process_branch.assert_not_called()


class TestProcessBranch:
    def setup_method(self):
        self.gitlab = MagicMock()
        self.config = MagicMock()
        self.config.config_dir = "/tmp"
        self.processor = FilesProcessor(self.gitlab, self.config, strict=False)
        self.processor.gl = MagicMock()

        # Stub the file-modification call so we can observe it without touching GitLab
        self.processor.modify_file_dealing_with_branch_protection = MagicMock()
        # Make templating a no-op pass-through so we don't depend on jinja
        self.processor.get_file_content_as_template = MagicMock(side_effect=lambda content, *a, **kw: content)

        self.branch = _make_branch("main")
        self.project = MagicMock()

    def _config(self, **file_opts):
        return _ConfigDict({"files": {"README.md": {**file_opts}}})

    def test_content_and_file_both_set_exits(self):
        cfg = self._config(content="hi", file="/x")
        with pytest.raises(SystemExit):
            self.processor.process_branch(self.branch, cfg, "README.md", self.project, "g/p")

    def test_delete_existing_file(self):
        cfg = self._config(delete=True)
        existing_file = MagicMock()
        self.project.files.get.return_value = existing_file

        self.processor.process_branch(self.branch, cfg, "README.md", self.project, "g/p")

        self.processor.modify_file_dealing_with_branch_protection.assert_called_once_with(
            self.project, self.branch, existing_file, "delete", cfg
        )

    def test_delete_missing_file_noop(self):
        cfg = self._config(delete=True)
        self.project.files.get.side_effect = GitlabGetError("not found")

        self.processor.process_branch(self.branch, cfg, "README.md", self.project, "g/p")

        self.processor.modify_file_dealing_with_branch_protection.assert_not_called()

    def test_create_with_content_when_file_missing(self):
        cfg = self._config(content="new content")
        self.project.files.get.side_effect = GitlabGetError("not found")

        self.processor.process_branch(self.branch, cfg, "README.md", self.project, "g/p")

        self.processor.modify_file_dealing_with_branch_protection.assert_called_once_with(
            self.project, self.branch, "README.md", "add", cfg, "new content"
        )

    def test_modify_when_content_differs_and_overwrite(self):
        cfg = self._config(content="new", overwrite=True)
        repo_file = MagicMock()
        repo_file.decode.return_value = b"old"
        self.project.files.get.return_value = repo_file

        self.processor.process_branch(self.branch, cfg, "README.md", self.project, "g/p")

        self.processor.modify_file_dealing_with_branch_protection.assert_called_once_with(
            self.project, self.branch, repo_file, "modify", cfg, "new"
        )

    def test_no_change_when_overwrite_false(self):
        cfg = self._config(content="new", overwrite=False)
        repo_file = MagicMock()
        repo_file.decode.return_value = b"old"
        self.project.files.get.return_value = repo_file

        self.processor.process_branch(self.branch, cfg, "README.md", self.project, "g/p")

        self.processor.modify_file_dealing_with_branch_protection.assert_not_called()

    def test_no_change_when_content_matches(self):
        cfg = self._config(content="same", overwrite=True)
        repo_file = MagicMock()
        repo_file.decode.return_value = b"same"
        self.project.files.get.return_value = repo_file

        self.processor.process_branch(self.branch, cfg, "README.md", self.project, "g/p")

        self.processor.modify_file_dealing_with_branch_protection.assert_not_called()

    def test_reads_file_from_absolute_path(self, tmp_path):
        content_file = tmp_path / "src.txt"
        content_file.write_text("from-file")

        cfg = self._config(file=str(content_file))
        self.project.files.get.side_effect = GitlabGetError("not found")

        self.processor.process_branch(self.branch, cfg, "README.md", self.project, "g/p")

        args = self.processor.modify_file_dealing_with_branch_protection.call_args[0]
        assert args[3] == "add" and args[5] == "from-file"

    def test_reads_file_from_relative_path(self, tmp_path):
        (tmp_path / "src.txt").write_text("relative-content")
        self.config.config_dir = str(tmp_path)

        cfg = self._config(file="src.txt")
        self.project.files.get.side_effect = GitlabGetError("not found")

        self.processor.process_branch(self.branch, cfg, "README.md", self.project, "g/p")

        args = self.processor.modify_file_dealing_with_branch_protection.call_args[0]
        assert args[5] == "relative-content"

    def test_templating_disabled_skips_jinja(self):
        cfg = self._config(content="hello", template=False)
        self.project.files.get.side_effect = GitlabGetError("not found")

        self.processor.process_branch(self.branch, cfg, "README.md", self.project, "g/p")

        self.processor.get_file_content_as_template.assert_not_called()

    def test_templating_enabled_by_default(self):
        cfg = self._config(content="hello")
        self.project.files.get.side_effect = GitlabGetError("not found")

        self.processor.process_branch(self.branch, cfg, "README.md", self.project, "g/p")

        self.processor.get_file_content_as_template.assert_called_once()
