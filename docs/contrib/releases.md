# Releases

## Versioning

We try to follow the [PEP 440](https://peps.python.org/pep-0440/) versioning scheme, which is mostly based on [semantic versioning](https://semver.org/).

## Procedure

The tooling relies on commit messages which follow the [conventional-commit format](https://www.conventionalcommits.org/en/v1.0.0/#summary) in order to produce consistent human and machine-readable commit messages.

1. We use [`release-please`](https://github.com/googleapis/release-please) to automate Version Bumps and CHANGELOG updates
2. Release-Please reads the commits since last release and automatically generates a Changelog and Opens a PR
3. To create a new Release we should merge in the "Release PR" created by [Release-Please github action](https://github.com/google-github-actions/release-please-action)

## Post GitHub Release Actions
Actions such as releasing to PyPi and GCHR must take place within `release-please.yml` rather than standalone workflows running on tag pushes because of limitations in the `GITHUB_TOKEN`: [Triggering a workflow from a workflow](https://docs.github.com/en/actions/using-workflows/triggering-a-workflow).

A `release_created` boolean is exposed by the `release-please` job to denote if it acted to create a Release PR or to create a GitHub Release, which can be consumed in later Jobs to determine when to trigger, for example:

```yaml
  publish:
    needs:
      - release-please
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        if: ${{ needs.release-please.outputs.release_created }}
```