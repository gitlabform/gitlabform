#!/bin/bash

set -euo pipefail

# based on https://stackoverflow.com/a/28709668/2693875 and https://stackoverflow.com/a/23006365/2693875
cecho() {
  if [[ $TERM == "dumb" ]]; then
    echo $2
  else
    local color=$1
    local exp=$2
    if ! [[ $color =~ ^[0-9]$ ]] ; then
       case $(echo "$color" | tr '[:upper:]' '[:lower:]') in
        bk | black) color=0 ;;
        r | red) color=1 ;;
        g | green) color=2 ;;
        y | yellow) color=3 ;;
        b | blue) color=4 ;;
        m | magenta) color=5 ;;
        c | cyan) color=6 ;;
        w | white|*) color=7 ;; # white or invalid color
       esac
    fi
    tput setaf $color
    # shellcheck disable=SC2086
    echo $exp
    tput sgr0
  fi
}

script_directory="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
repo_root_directory="$script_directory/.."

if [[ $# == 1 ]] ; then
  gitlab_version="$1"
else
  gitlab_version="latest"
fi

cecho b "Pulling GitLab image version '$gitlab_version'..."
docker pull gitlab/gitlab-ee:$gitlab_version

cecho b "Preparing to start GitLab..."
stop_gitlab() {
  existing_gitlab_container_id=$(docker ps -a -f "name=gitlab" --format "{{.ID}}")
  if [[ -n $existing_gitlab_container_id ]] ; then
    cecho b "Stopping and removing GitLab container..."
    docker stop --time=30 "$existing_gitlab_container_id"
    docker rm "$existing_gitlab_container_id"
    rm -rf "$repo_root_directory"/config
    rm -rf "$repo_root_directory"/logs
    rm -rf "$repo_root_directory"/data
  else
    cecho b "No existing GitLab container running."
  fi
}
stop_gitlab

mkdir -p "$repo_root_directory"/config
if [[ -f Gitlab.gitlab-license ]] ; then
  cecho b "EE license file found - using it..."
  cp Gitlab.gitlab-license "$repo_root_directory"/config/
fi
mkdir -p "$repo_root_directory"/logs
mkdir -p "$repo_root_directory"/data

cecho b "Starting GitLab..."
# run GitLab with root password pre-set and as many unnecessary features disabled to speed up the startup
container_id=$(docker run --detach \
    --hostname gitlab.foobar.com \
    --env GITLAB_OMNIBUS_CONFIG="gitlab_rails['initial_root_password'] = 'password'; registry['enable'] = false; grafana['enable'] = false; prometheus_monitoring['enable'] = false;" \
    --publish 443:443 --publish 80:80 --publish 2022:22 \
    --name gitlab \
    --restart always \
    --volume "$repo_root_directory/dev/healthcheck-and-setup.sh:/healthcheck-and-setup.sh" \
    --health-cmd '/healthcheck-and-setup.sh' \
    --health-interval 2s \
    --health-timeout 2m \
    gitlab/gitlab-ee:$gitlab_version)

cecho b "Waiting 3 minutes before starting to check if GitLab has started..."
cecho b "(Run this in another terminal you want to follow the instance logs:"
cecho y "docker logs -f ${container_id}"
cecho b ")"
sleep 3m

"$script_directory"/await-healthy.sh

# create files with params needed by the tests to access GitLab
# (we are using these files to pass values from this script to the outside bash shell
# - we cannot change its env variables from inside it)
echo "http://localhost" > "$repo_root_directory"/gitlab_url.txt
echo "token-string-here123" > "$repo_root_directory"/gitlab_token.txt

cecho b 'Starting GitLab complete!'
echo ''
cecho b 'GitLab version:'
curl -H "Authorization:Bearer $(cat "$repo_root_directory"/gitlab_token.txt)" http://localhost/api/v4/version
echo ''
cecho b 'GitLab web UI URL (user: root, password: password)'
echo 'http://localhost'
echo ''

cecho b 'Run this command to stop GitLab container and DELETE the data in it:'
cecho r 'stop_gitlab'
echo ''

cecho b 'To restart GitLab container again, re-run this script.'
echo ''

cecho b 'Run this to start the acceptance tests:'
echo ''
cecho y 'pytest tests/acceptance'
