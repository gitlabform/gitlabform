#!/bin/bash
tags=""
version="$(cat version)"
for os in alpine debian
do
    effective_version="${os}_version"
    suffix="${os}${!effective_version}"
    docker build \
        --build-arg PY_VERSION=$python_version \
        --build-arg OS_VERSION="${!effective_version}" \
        --file "${os}.Dockerfile" \
        --tag "egnyte/gitlabform:latest-${suffix}" .
    tags="$tags egnyte/gitlabform:latest-${suffix}"

    docker tag "egnyte/gitlabform:latest-${suffix}" "egnyte/gitlabform:${version}-${suffix}"
    tags="$tags !$"

    if [ "$os" = "alpine" ]
    then
        docker tag "egnyte/gitlabform:latest-${suffix}" "egnyte/gitlabform:latest"
        tags="$tags !$"
    fi
done

for image in $tags
do
    docker push $image
done