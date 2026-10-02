# Releases

## Versioning

We try to follow the [PEP 440](https://peps.python.org/pep-0440/) versioning scheme, which is mostly based on [semantic versioning](https://semver.org/).

## Procedure

1. Make sure you're on `main` branch and it is up-to-date.
2. Add an entry in [changelog.md](../changelog.md). Remember to give thanks to all the contributors! Commit this change.
3. Update version using [`tbump`](https://github.com/your-tools/tbump). Run `pipx run tbump <new-semantic-version-number>`.

    **Note**: You may need to install `pipx` first if it's not already installed. Follow the instructions at [`pipx` documentation](https://pypa.github.io/pipx/installation/).

    Executing `tbump` will create a commit containing version updates to necessary files (i.e. `tbump.toml`, `pyproject.toml`), create a new tag from for the new version from the current `ref` in `main` branch, and finally push the commits and tag to remote.

    When the version tag is created, the release workflow will do the following:

    - validate that the upstream Main workflow passed for the same commit and that the tag points to that commit
    - upload the new version of gitlabform to [PyPI](https://pypi.org/project/gitlabform/)
    - create the corresponding [GitHub release](https://github.com/gitlabform/gitlabform/releases) that references the new tag
    - promote the already published SHA-tagged Docker image to release tags such as `vX.Y.Z`, `vX.Y`, and `vX` using `docker buildx imagetools create`

    The immutable `sha-<full-sha>` and `sha-<short-sha>` Docker tags are created earlier, as part of the successful main-branch publication flow, and are not created as part of the version-tag release procedure itself.

    The release workflow can also be triggered manually, in which case it requires a release version tag and the corresponding main workflow run id.

4. Edit the release in GitHub and copy the changelog entry into its description.

## Docker publication model

The Docker image is built and verified by the reusable `build.yml` workflow, and the resulting artifacts are then published by the release pipeline.

This avoids rebuilding the image during the final release step and keeps PR validation free of registry credentials. The image that gets promoted to the semver tags is always the already published `sha-<head_sha>` image from the successful main-branch publication flow.
