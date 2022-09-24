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

if [[ $(uname -s) == 'Darwin' ]] && [[ $(uname -m) == 'arm64' ]] ; then
  gitlab_image="gsdukbh/gitlab-ee-arm64"
else
  gitlab_image="gitlab/gitlab-ee"
fi

cecho b "Pulling GitLab image version '$gitlab_version'..."
docker pull $gitlab_image:$gitlab_version

cecho b "Preparing to start GitLab..."
existing_gitlab_container_id=$(docker ps -a -f "name=gitlab" --format "{{.ID}}")
if [[ -n $existing_gitlab_container_id ]] ; then
  cecho b "Stopping and removing existing GitLab container..."
  docker stop --time=30 "$existing_gitlab_container_id"
  docker rm "$existing_gitlab_container_id"
fi

gitlab_omnibus_config="gitlab_rails['initial_root_password'] = 'password'; registry['enable'] = false; grafana['enable'] = false; prometheus_monitoring['enable'] = false;"

cecho b "Starting GitLab..."
# run GitLab with root password pre-set and as many unnecessary features disabled to speed up the startup
docker run --detach \
    --hostname gitlab.foobar.com \
    --env GITLAB_OMNIBUS_CONFIG="$gitlab_omnibus_config" \
    --publish 443:443 --publish 80:80 --publish 2022:22 \
    --name gitlab \
    --restart always \
    --volume "$repo_root_directory/dev/healthcheck-and-setup.sh:/healthcheck-and-setup.sh" \
    --health-cmd '/healthcheck-and-setup.sh' \
    --health-interval 2s \
    --health-timeout 2m \
    $gitlab_image:$gitlab_version

cecho b "Waiting 2 minutes before starting to check if GitLab has started..."
cecho b "(Run this in another terminal you want to follow the instance logs:"
cecho y "docker logs -f gitlab"
cecho b ")"
sleep 120

$script_directory/await-healthy.sh

# create files with params needed by the tests to access GitLab
# (we are using these files to pass values from this script to the outside bash shell
# - we cannot change its env variables from inside it)
echo "http://localhost" > $repo_root_directory/gitlab_url.txt
echo "token-string-here123" > $repo_root_directory/gitlab_token.txt

cecho b 'Starting GitLab complete!'
echo ''
cecho b 'GitLab version:'
curl -s -H "Authorization:Bearer $(cat $repo_root_directory/gitlab_token.txt)" http://localhost/api/v4/version
echo ''
if [[ -n "${GITLAB_EE_LICENSE:-}" ]] ; then
  echo "{\"license\":\"$GITLAB_EE_LICENSE\"}" > $repo_root_directory/gitlab-license.json
fi
if [[ -f $repo_root_directory/gitlab-license.json ]] ; then
  cecho b 'Loading GitLab license...'
  curl -s -X POST -H "Authorization:Bearer $(cat $repo_root_directory/gitlab_token.txt)" -H "Content-Type: application/json" -d @$repo_root_directory/gitlab-license.json http://localhost/api/v4/license >/dev/null 2>&1

  cecho b 'GitLab license (plan, is expired?):'
  curl -s -H "Authorization:Bearer $(cat $repo_root_directory/gitlab_token.txt)" http://localhost/api/v4/license | jq '.plan, .expired'
  echo ''
fi
cecho b 'GitLab web UI URL (user: root, password: password)'
echo 'http://localhost'
echo ''
cecho b 'You can run these commands to stop and delete the GitLab container:'
cecho r "docker stop --time=30 gitlab"
cecho r "docker rm gitlab"
echo ''
cecho b 'To start GitLab container again, re-run this script. Note that GitLab will NOT keep any data'
cecho b 'so the start will take a lot of time again. (But this is the only way to make GitLab in Docker stable.)'
echo ''
cecho b 'Run this to start the acceptance tests (it will automatically load GITLAB_URL from gitlab_url.txt'
cecho b 'and GITLAB_TOKEN from gitlab_token.txt created by this script):'
echo ''
cecho y 'pytest tests/acceptance'
