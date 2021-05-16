#!/bin/bash

# inputs:
#   os
#   docker_username
#   docker_password
#   release_type

set -ue

python_version="3.9"
version="$(< version)"

effective_version="${os}_version"
suffix="${!effective_version}"

image_name="egnyte/gitlabform"
default_tag="${image_name}:${version}-${suffix}"
os_latest="${image_name}:latest-${suffix}"
latest="${image_name}:latest"
tags=( )

docker pull "${os_latest}" || echo "no cache is available"

docker build \
  --build-arg PY_VERSION="${python_version}" \
  --build-arg OS_VERSION="${!effective_version}" \
  --file "dev/${os}.Dockerfile" \
  --tag "${default_tag}" .
tags+=( "${default_tag}" )

if [[ "${release_type:-}" == "public" ]]; then
  docker tag "${default_tag}" "${os_latest}" 
  tags+=( "${os_latest}" )

  # we treat alpine image as the main one, so it gets the plain "latest" tag
  if [[ "${os}" = "alpine" ]]; then
    docker tag "${default_tag}" "${latest}"
    tags+=( "${latest}" )
  fi
fi

echo "Tags to be published:"
for tag in "${tags[@]}"; do
  printf "  * %s\n" "${tag}"
done

echo "$docker_password" | docker login -u "$docker_username" --password-stdin
for tag in "${tags[@]}"; do
  docker push "${tag}"
done
