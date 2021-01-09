#!/bin/bash

# inputs:
#   os
#   docker_username
#   docker_password

python_version="3.8"
tags=""
version="$(cat version)"

effective_version="${os}_version"
suffix="${!effective_version}"
latest="egnyte/gitlabform:latest-${suffix}"

docker pull "${latest}" || echo "no cache is available"
docker build \
  --build-arg PY_VERSION="${python_version}" \
  --build-arg OS_VERSION="${!effective_version}" \
  --file "dev/${os}.Dockerfile" \
  --tag "${latest}" .
tags="$tags ${latest}"

docker tag "${latest}" "egnyte/gitlabform:${version}-${suffix}"
tags="$tags egnyte/gitlabform:${version}-${suffix}"

# we treat alpine image as the main one, so it gets the plain "latest" tag
if [ "${os}" = "alpine" ]
then
  docker tag "${latest}" "egnyte/gitlabform:latest"
  tags="$tags egnyte/gitlabform:latest"
fi

for image in ${tags}
do
#  echo "$docker_password" | docker login -u "$docker_username" --password-stdin
#  docker push "${image}"
   echo "${image}"
done
