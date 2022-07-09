# Quick Start

Let's assume that you want to add a deployment key to all projects in a group "My Group" (with path "my-group").
If so then:

1. Create example `config.yml`:

```yaml
config_version: 3

gitlab:
  url: https://gitlab.yourcompany.com
  # alternatively use the GITLAB_TOKEN environment variable for this
  token: "<private token OR an OAuth2 access token of an admin user>"

projects_and_groups:
  my-group/*:
    deploy_keys:
      a_friendly_deploy_key_name:  # this name is only used in GitLabForm config
        key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC3WiHAsm2UTz2dU1vKFYUGfHI1p5fIv84BbtV/9jAKvZhVHDqMa07PgVtkttjvDC8bA1kezhOBKcO0KNzVoDp0ENq7WLxFyLFMQ9USf8LmOY70uV/l8Gpcn1ZT7zRBdEzUUgF/PjZukqVtuHqf9TCO8Ekvjag9XRfVNadKs25rbL60oqpIpEUqAbmQ4j6GFcfBBBPuVlKfidI6O039dAnDUsmeafwCOhEvQmF+N5Diauw3Mk+9TMKNlOWM+pO2DKxX9LLLWGVA9Dqr6dWY0eHjWKUmk2B1h1HYW+aUyoWX2TGsVX9DlNY7CKiQGsL5MRH9IXKMQ8cfMweKoEcwSSXJ
        title: ssh_key_name_that_is_shown_in_gitlab
        can_push: false
```
2. Run:
```shell
docker run -it -v $(pwd):/config ghcr.io/gitlabform/gitlabform:latest gitlabform my-group
```
3. Watch GitLabForm add this deploy key to all projects in "My Group" group in your GitLab!
