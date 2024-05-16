# Releases

## Versioning

We try to follow the [PEP 440](https://peps.python.org/pep-0440/) versioning scheme, which is mostly based on [semantic versioning](https://semver.org/).

## Procedure

1. Make sure you're on `main` branch and it is up-to-date.
2. Add an entry in [changelog.md](../changelog.md). Remember to give thanks to all the contributors! Commit this change.
3. Update version using [`tbump`](https://github.com/your-tools/tbump). Run `pipx run tbump <new-semantic-version-number>`.

    **Note**: You may need to install `pipx` first if it's not already installed. Follow the instructions at [`pipx` documentation](https://pypa.github.io/pipx/installation/).

    Executing `tbump` will create a commit containing version updates to necessary files (i.e. `tbump.toml`, `version`), create a new tag from for the new version from the current `ref` in `main` branch, and finally push the commits and tag to remote.

    Following the above steps when a new tag is created, GitHub Action workflow will do following:

    - Create a docker image containing new version of gitlabform and publish to [github's package registry under gitlabform](https://github.com/gitlabform/gitlabform/pkgs/container/gitlabform).
    - Upload new version of gitlabform to [pypi package registry under gitlabform](https://pypi.org/project/gitlabform/).
    - A corresponding [GitHub release](https://github.com/gitlabform/gitlabform/releases) will be created that references the new tag.

3. Edit the release in GitHub and copy the changelog entry into its description.
