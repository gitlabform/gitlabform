#!/bin/bash

# inputs:
#   os
#   docker_username
#   docker_password

python_version="3.8"
version="$(cat version)"

set -ue

effective_version="${os}_version"
suffix="${!effective_version}"
image_name="egnyte/gitlabform:${version}-${suffix}"
os_latest="egnyte/gitlabform:latest-${suffix}"

docker pull "${os_latest}" || echo "no cache is available"
docker build \
  --build-arg PY_VERSION="${python_version}" \
  --build-arg OS_VERSION="${!effective_version}" \
  --file "dev/${os}.Dockerfile" \
  --tag "${image_name}" .

tags=( "${image_name}" )

# TODO: something more clever here maybe?
# TODO: do we need to validate the version?
if ! [[ "${version}" =~ .+rc.+ ]]; then
  docker tag "${image_name}" "${os_latest}" 
  tags+=( "${os_latest}" )

  # we treat alpine image as the main one, so it gets the plain "latest" tag
  if [[ "${os}" = "alpine" ]]; then
    latest=egnyte/gitlabform:latest
    docker tag "${image_name}" "${latest}"
    tags+=( "${latest}" )
  fi
fi

echo "Images to be published: ${tags[*]}"
for image in "${tags[@]}"; do
  echo "$docker_password" | docker login -u "$docker_username" --password-stdin
  docker push "${image}"
done
