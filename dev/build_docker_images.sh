#!/bin/bash

# inputs:
#   os
#   docker_username
#   docker_password
#   GITHUB_REF

python_version="3.8"
version="$(cat version)"

git_tag="${GITHUB_REF#refs/tags/*}"
if [[ "${git_tag}" != "${version}" ]]; then
  >&2 echo "ERROR: Mismatch between Git tag ${git_tag} and version file ${version}" 
  exit 1
fi

image_name="egnyte/gitlabform:${version}-${suffix}"
effective_version="${os}_version"
suffix="${!effective_version}"
os_latest="egnyte/gitlabform:latest-${suffix}"

docker pull "${os_latest}" || echo "no cache is available"
docker build \
  --build-arg PY_VERSION="${python_version}" \
  --build-arg OS_VERSION="${!effective_version}" \
  --file "dev/${os}.Dockerfile" \
  --tag "${image_name}" .

tags=( "${image_name}" )

docker tag "${image_name}" "${os_latest}" 
tags+=( "${latest}" )

# we treat alpine image as the main one, so it gets the plain "latest" tag
if [[ "${os}" = "alpine" ]]; then
  latest=egnyte/gitlabform:latest
  docker tag "${image_name}" "${latest}"
  tags+=( "${latest}" )
fi

for image in "${tags[@]}"; do
  echo "$docker_password" | docker login -u "$docker_username" --password-stdin
  docker push "${image}"
done
