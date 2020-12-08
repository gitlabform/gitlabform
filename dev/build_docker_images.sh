#!/bin/bash
tags=""
version="$(cat version)"
python_version="3.8"
for os in alpine debian
do
    effective_version="${os}_version"
    suffix="${!effective_version}"
    latest="egnyte/gitlabform:latest-${suffix}"
    docker pull "${latest}" || echo "no cache is available"
    docker build \
        --build-arg PY_VERSION=$python_version \
        --build-arg OS_VERSION="${!effective_version}" \
        --file "dev/${os}.Dockerfile" \
        --tag "${latest}" .
    tags="$tags ${latest}"

    docker tag "${latest}" "egnyte/gitlabform:${version}-${suffix}"
    tags="$tags egnyte/gitlabform:${version}-${suffix}"

    if [ "$os" = "alpine" ]
    then
        docker tag "${latest}" "egnyte/gitlabform:latest"
        tags="$tags egnyte/gitlabform:latest"
    fi
done

for image in $tags
do
    if [ ! -z "${push_images}" ]
    then
        echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
        docker push $image
    else
        echo "$image"
    fi
done
