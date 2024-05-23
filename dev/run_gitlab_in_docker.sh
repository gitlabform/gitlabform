#!/usr/bin/env bash

# ============================================================================
#  GitLab Deployment Script
#
#  This script pulls the specified GitLab Docker image, stops and removes any
#  existing GitLab container, configures the necessary volumes and environment,
#  and starts a new GitLab container with predefined settings.
#
#  It also generates files with the GitLab URL and access token for use in
#  other scripts or tests.
# ============================================================================

# ============================================================================
#  Functions
# ============================================================================

# Print colored output
cecho() {
  local color=$1 text=$2

  if [[ $TERM == "dumb" ]]; then
    echo "$text"
    return
  fi

  case $(echo "$color" | tr '[:upper:]' '[:lower:]') in
    bk | black) color=0 ;;
    r | red)    color=1 ;;
    g | green)  color=2 ;;
    y | yellow) color=3 ;;
    b | blue)   color=4 ;;
    m | magenta)color=5 ;;
    c | cyan)   color=6 ;;
    w | white | *) color=7 ;; # white or invalid color
  esac

  tput setaf "$color"
  echo -e "$text"
  tput sgr0
}

# ============================================================================
#  Variables
# ============================================================================

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
repo_root_dir="$script_dir/.."

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

# ============================================================================
#  Main Logic
# ============================================================================

# Pull the GitLab Docker image
cecho b "Pulling GitLab image version '$gitlab_version'..."
docker pull "$gitlab_image:$gitlab_version"

# Stop and remove any existing GitLab container
cecho b "Preparing to start GitLab..."
existing_container_id=$(docker ps -a -f "name=gitlab" --format "{{.ID}}")
if [[ -n $existing_container_id ]]; then
  cecho b "Stopping and removing existing GitLab container..."
  docker stop --time=30 "$existing_container_id"
  docker rm "$existing_container_id"
fi

# Configure volumes and environment
if [[ -f "$repo_root_dir/Gitlab.gitlab-license" || -n "${GITLAB_EE_LICENSE:-}" ]]; then
  mkdir -p "$repo_root_dir/config"
  rm -rf "$repo_root_dir/config/*"

  if [[ -f "$repo_root_dir/Gitlab.gitlab-license" ]]; then
    cecho b "EE license file found - using it..."
    cp "$repo_root_dir/Gitlab.gitlab-license" "$repo_root_dir/config/"
  else
    cecho b "EE license env variable found - using it..."
    echo "$GITLAB_EE_LICENSE" > "$repo_root_dir/config/Gitlab.gitlab-license"
  fi

  config_volume="--volume $repo_root_dir/config:/etc/gitlab"
else
  config_volume=""
fi

# Start a new GitLab container
cecho b "Starting GitLab..."
docker run --detach \
  --hostname localhost \
  --publish 443:443 --publish 80:80 --publish 2022:22 \
  --name gitlab \
  --restart always \
  --volume "$repo_root_dir/dev/healthcheck-and-setup.sh:/healthcheck-and-setup.sh" \
  --volume "$repo_root_dir/dev/gitlab.rb:/etc/gitlab/gitlab.rb" \
  $config_volume \
  --health-cmd '/healthcheck-and-setup.sh' \
  --health-interval 2s \
  --health-timeout 2m \
  "$gitlab_image:$gitlab_version"

cecho b "Waiting 2 minutes before checking if GitLab has started..."
cecho b "(Run this in another terminal to follow the instance logs:"
cecho y "docker logs -f gitlab"
cecho b ")"
sleep 120

"$script_dir/await-healthy.sh"

# Generate files with GitLab URL and access token
echo "http://localhost" > "$repo_root_dir/gitlab_url.txt"
echo "token-string-here123" > "$repo_root_dir/gitlab_token.txt"

# Display GitLab information
cecho b 'GitLab started successfully!'
echo ''
cecho b 'GitLab version:'
curl -s -H "Authorization:Bearer $(cat "$repo_root_dir/gitlab_token.txt")" http://localhost/api/v4/version
echo ''

if [[ -f "$repo_root_dir/Gitlab.gitlab-license" || -n "${GITLAB_EE_LICENSE:-}" ]]; then
  cecho b 'GitLab license (plan, is expired?):'
  curl -s -H "Authorization:Bearer $(cat "$repo_root_dir/gitlab_token.txt")" http://localhost/api/v4/license | jq '.plan, .expired'
  echo ''
fi

cecho b 'GitLab web UI URL (user: root, password: mK9JnG7jwYdFcBNoQ3W3 )'
echo 'http://localhost'
echo ''

# Provide instructions for stopping and starting GitLab
cecho b 'To stop and delete the GitLab container, run:'
cecho r "docker stop --time=30 gitlab"
cecho r "docker rm gitlab"
echo ''

cecho b 'To start GitLab container again, re-run this script.'
cecho b 'Note: GitLab will NOT keep any data, so the start will take time.'
cecho b '(This is the only way to make GitLab in Docker stable.)'
echo ''

cecho b 'To start the acceptance tests, run:'
cecho y 'pytest tests/acceptance'
echo ''