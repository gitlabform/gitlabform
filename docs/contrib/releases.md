# Releases

## Versioning

We try to follow the [PEP 440](https://peps.python.org/pep-0440/) versioning scheme, which is mostly based on [semantic versioning](https://semver.org/).

## Procedure

1. Commit following changes either as a PR to `main` branch or directly to `main`
    * Add an entry in [changelog.md](../changelog.md). Remember to give thanks to all the contributors!
    * Update `tbump` file to bump the version.

        ```toml
        [version]
        # Set the new version as `current`
        current = "1.2.3"
        ```

    * Update `version` file to bump the version.

2. Create a tag for the new version, `v1.2.3`, from the latest of `main` that includes the above changes.

    ```shell
    $ git checkout main
    Switched to branch 'main'
    Your branch is up to date with 'upstream/main'.
    $ git pull
    Already up to date.
    $ git tag v1.2.3
    $ git push upstream v1.2.3
    ```

    Creating a new tag will launch GitHub Action workflow that will do following:

    - Create a docker image containing new version of gitlabform and publish to [github's package registry under gitlabform](https://github.com/gitlabform/gitlabform/pkgs/container/gitlabform).
    - Upload new version of gitlabform to [pypi package registry under gitlabform](https://pypi.org/project/gitlabform/).
    - A corresponding [GitHub release](https://github.com/gitlabform/gitlabform/releases) will be created that references the new tag.

3. Edit the release in GitHub and copy the changelog entry into its description.
