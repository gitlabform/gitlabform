from gitlabform.processors.util.mirrors import (
    mask_mirror_url_credentials,
    normalize_mirror_url_for_comparison,
)


class TestNormalizeMirrorUrlForComparison:
    def test_strips_credentials(self):
        assert (
            normalize_mirror_url_for_comparison("https://user:token@example.com/repo.git")
            == "https://example.com/repo.git"
        )

    def test_strips_masked_credentials(self):
        assert (
            normalize_mirror_url_for_comparison("https://*****:*****@example.com/repo.git")
            == "https://example.com/repo.git"
        )

    def test_url_without_credentials_is_unchanged(self):
        assert normalize_mirror_url_for_comparison("ssh://example.com/repo.git") == "ssh://example.com/repo.git"


class TestMaskMirrorUrlCredentials:
    def test_masks_credentials(self):
        assert (
            mask_mirror_url_credentials("https://user:token@example.com/repo.git")
            == "https://*****:*****@example.com/repo.git"
        )

    def test_url_without_credentials_is_unchanged(self):
        assert mask_mirror_url_credentials("https://example.com/repo.git") == "https://example.com/repo.git"
