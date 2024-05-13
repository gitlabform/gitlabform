# Releases

## Versioning

We try to follow the [PEP 440](https://peps.python.org/pep-0440/) versioning scheme, which is mostly based on [semantic versioning](https://semver.org/).

## Procedure

The tooling relies on commit messages which follow the [conventional-commit format](https://www.conventionalcommits.org/en/v1.0.0/#summary) in order to produce consistent human and machine-readable commit messages.

1. We use [`release-please`](https://github.com/googleapis/release-please) to automate Version Bumps and CHANGELOG updates
2. Release-Please reads the commits since last release and automatically generates a Changelog and Opens a PR
3. To create a new Release we should merge in the "Release PR" created by [Release-Please github action](https://github.com/google-github-actions/release-please-action)
