# Releases

## Versioning

We try to follow the [PEP 440](https://peps.python.org/pep-0440/) versioning scheme, which is mostly based on [semantic versioning](https://semver.org/).

## Procedure

1. Make sure you're on `main` branch and it is up-to-date.
2. Add an entry in [changelog.md](../changelog.md). Remember to give thanks to all the contributors! Commit this change.
3. Update version using [`tbump`](https://github.com/your-tools/tbump). Run `pipx run tbump <new-semantic-version-number>`.

    **Note**: You may need to install `pipx` first if it's not already installed. Follow the instructions at [`pipx` documentation](https://pypa.github.io/pipx/installation/).

    Executing `tbump` will create a commit containing version updates to necessary files (i.e. `tbump.toml`, `pyproject.toml`), create a new tag from for the new version from the current `ref` in `main` branch, and finally push the commits and tag to remote.

    Following the above steps when a new tag is created, GitHub Action workflow will do following:

    - Create a docker image containing new version of gitlabform and publish to [github's package registry under gitlabform](https://github.com/gitlabform/gitlabform/pkgs/container/gitlabform).
    - Upload new version of gitlabform to [pypi package registry under gitlabform](https://pypi.org/project/gitlabform/).
    - A corresponding [GitHub release](https://github.com/gitlabform/gitlabform/releases) will be created that references the new tag.
    - Attach an SBOM and signed attestations to each of them, see [Supply chain artifacts](#supply-chain-artifacts).

    The release workflow also verifies that the commit on `main` passed the build and quality. It will trigger a release workflow that will proceed only if a corresponding version tag exists in GitHub and main branch workflow on that commit passed. The release workflow can also be triggered manually, which will require 2 inputs: a release version tag and main branch workflow's run id from corresponding commit.

    The publish jobs run in order: GitHub release, then PyPI, then GHCR. If one fails, nothing after it is published. Fix the cause and rerun the failed jobs: the GitHub release is updated in place and the rest is published then. Within the GHCR job the image tags are pushed before the signed attestations are attached, so if a later step of that job fails, the tags are already public without them. Rerunning the job rebuilds and republishes the tags and attaches the attestations.

3. Edit the release in GitHub and copy the changelog entry into its description.

## Supply chain artifacts

Every release comes with a software bill of materials (SBOM) and attestations signed keyless with [Sigstore](https://www.sigstore.dev/), using the identity of the release workflow.

| Artifact | SBOM | Signed attestations |
|---|---|---|
| GitHub release | `gitlabform-<version>.cdx.json` asset ([CycloneDX](https://cyclonedx.org/)), the package and its locked runtime dependencies from `uv.lock` | the same SBOM, attested on the wheel and sdist |
| PyPI package | | [PEP 740](https://peps.python.org/pep-0740/) publish attestations, shown as verified provenance on [pypi.org](https://pypi.org/project/gitlabform/#files) |
| Docker image | SPDX SBOM per platform, made by buildx and attached to the image index | build provenance on the index, the per-platform SBOMs on each platform manifest |

The CycloneDX SBOM covers the Python side only. Installing from PyPI on other platforms may resolve transitive dependencies differently. The image SBOMs also cover the Alpine packages.

### Verifying a release

Attestations are stored on GitHub and can be checked with the [GitHub CLI](https://cli.github.com/). Without `--predicate-type` it looks for build provenance only.

```shell
# the Docker image: build provenance
gh attestation verify oci://ghcr.io/gitlabform/gitlabform:<version> --repo gitlabform/gitlabform

# the Docker image: SBOM of one platform
digest=$(docker buildx imagetools inspect ghcr.io/gitlabform/gitlabform:<version> --format '{{ json .Manifest }}' \
  | jq -r '.manifests[] | select(.platform.architecture == "amd64") | .digest')
gh attestation verify oci://ghcr.io/gitlabform/gitlabform@$digest --repo gitlabform/gitlabform \
  --predicate-type https://spdx.dev/Document/v2.3

# a wheel or sdist downloaded from PyPI: SBOM
gh attestation verify gitlabform-<version>-py3-none-any.whl --repo gitlabform/gitlabform \
  --predicate-type https://cyclonedx.org/bom
```

Verification works on the digest, so it also holds for an image pulled through a mirror or proxy registry. The unsigned buildx SBOM can be read directly with `docker buildx imagetools inspect ghcr.io/gitlabform/gitlabform:<version> --format '{{ json .SBOM }}'`.
