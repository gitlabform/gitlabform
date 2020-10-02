#!/bin/bash

set -euo pipefail

# based on https://stackoverflow.com/a/28709668/2693875 and https://stackoverflow.com/a/23006365/2693875
cecho() {
  local exp=$2
  local color=$1
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
  echo "$exp"
  tput sgr0
}

cecho b "Starting GitLab..."

docker pull gitlab/gitlab-ee:latest

mkdir -p config
if [[ -f company.gitlab-license ]] ; then
  cecho b "EE license file found - using it..."
  cp company.gitlab-license config/
fi
mkdir -p logs
mkdir -p data

# run GitLab with root password pre-set and as many unnecessary features disabled to speed up the startup
docker run --detach \
    --hostname gitlab.foobar.com \
    --env GITLAB_OMNIBUS_CONFIG="gitlab_rails['initial_root_password'] = 'password'; registry['enable'] = false; grafana['enable'] = false; prometheus_monitoring['enable'] = false;" \
    --publish 443:443 --publish 80:80 --publish 2022:22 \
    --name gitlab \
    --restart always \
    --volume "$(pwd)/config:/etc/gitlab" \
    --volume "$(pwd)/logs:/var/log/gitlab" \
    --volume "$(pwd)/data:/var/opt/gitlab" \
    gitlab/gitlab-ee:latest

cecho b "Waiting 3 minutes before starting to check if GitLab has started..."
sleep 3m
until curl -X POST -s http://localhost/oauth/token | grep "The request is missing a required parameter" >/dev/null ; do
  cecho b "Waiting 5 more secs for GitLab to start..." ;
  sleep 5s ;
done

# get a root API access token for further operations...
echo 'grant_type=password&username=root&password=password' > auth.txt
curl --data "@auth.txt" -X POST -s http://localhost/oauth/token | jq -r .access_token > gitlab_token.txt

# ...and the GitLab URL, to make the output complete
echo "http://localhost" > gitlab_url.txt

cecho b 'Starting GitLab complete!'
echo ''
cecho b 'Run these commands to set the env variables needed by the tests to use this GitLab instance:'
# shellcheck disable=SC2016
cecho g 'export GITLAB_URL=$(cat gitlab_url.txt)'
# shellcheck disable=SC2016
cecho g 'export GITLAB_TOKEN=$(cat gitlab_token.txt)'
echo ''
cecho b 'Run this command to stop GitLab container:'
# shellcheck disable=SC2016
cecho r 'docker stop --time=30 $(docker ps -f "ancestor=gitlab/gitlab-ee" --format "{{.ID}}")'
echo ''
cecho b 'To start GitLab container again run above commands again. Note that GitLab will reuse existing ./data, ./config'
cecho b 'and ./logs dirs. To start new GitLab instance from scratch please delete them.'
echo ''
cecho b 'Run this to start the integration tests:'
echo ''
cecho y 'py.test gitlabform/gitlabform/test'
