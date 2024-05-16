# Releases

## Versioning

We try to follow the [PEP 440](https://peps.python.org/pep-0440/) versioning scheme, which is mostly based on [semantic versioning](https://semver.org/).

## Procedure

The tooling relies on commit messages which follow the [conventional-commit format](https://www.conventionalcommits.org/en/v1.0.0/#summary) in order to produce consistent human and machine-readable commit messages.

1. We use [`release-please`](https://github.com/googleapis/release-please) to automate Version Bumps and CHANGELOG updates
2. Release-Please reads the commits since last release and automatically generates a Changelog and Opens a PR
3. To create a new Release we should merge in the "Release PR" created by [Release-Please github action](https://github.com/google-github-actions/release-please-action)

## Release-Please Token
Due to limitations in [GITHUB_TOKEN](https://docs.github.com/en/actions/using-workflows/triggering-a-workflow); 
it cannot trigger other workflows on branches or tags, we use a [fine-grained personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token)
owned by the gitlabform repository.

This token requires Repository Access to gitlabform/gitlabform.

This token requires the following Permissions

### Repository Permissions
1. Actions: read/write
2. Attestations: read
3. Commit statuses: read
4. Contents: read/write
5. Metadata: read
6. Pull Requests: read/write
7. Secrets: read
8. Variables: read

### This Token Will Expire 15/04/2025