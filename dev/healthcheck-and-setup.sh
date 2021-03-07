#!/usr/bin/env sh

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


# This script is intended to be used as a Docker HEALTHCHECK for the GitLab container.
# It prepares GitLab prior to running acceptance tests.
#
# This is a known workaround for docker-compose lacking lifecycle hooks.
# See: https://github.com/docker/compose/issues/1809#issuecomment-657815188

set -e

# Check for a successful HTTP status code from GitLab.
curl --silent --show-error --fail --output /dev/null 127.0.0.1:80

# Because this script runs on a regular health check interval,
# this file functions as a marker that tells us if initialization already finished.
done=/var/gitlab-acctest-initialized

test -f $done || {
  echo 'Initializing GitLab for integration tests'

  # As documented at https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#programmatically-creating-a-personal-access-token
  # the token has to be at least 20 characters long - thus "token-string-here123".
  echo 'Creating access token'
  (
    printf 'gitlabform_token = PersonalAccessToken.create('
    printf 'user_id: 1, '
    printf 'scopes: [:api, :read_user], '
    printf 'name: :gitlabform);'
    printf "gitlabform_token.set_token('token-string-here123');"
    printf 'gitlabform_token.save!;'
  ) | gitlab-rails console

  touch $done
}

echo 'GitLab is ready for integration tests'
