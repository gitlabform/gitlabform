# GitLabForm

GitLabForm is an easy configuration as code tool for GitLab using config in plain YAML.

## Features

GitLabForm enables you to manage:

* Project settings,
* Deployment keys,
* Secret variables,
* Branches (protect/unprotect),
* Services,
* (Project) Hooks,
* (Add/edit or delete) Files,

...for a group of projects, single projects and a combination of them (default config on a group level + overrides
for particular projects).

## Quick start

1. Install with: `pip3 install gitlabform`

2. Create example `config.yml`:

```yaml
gitlab:
  url: https://gitlab.yourcompany.com
  token: "<private token of an admin user>"

group_settings:
  'my_group':
    deploy_keys:
      a_friendly_deploy_key_name:
        key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC3WiHAsm2UTz2dU1vKFYUGfHI1p5fIv84BbtV/9jAKvZhVHDqMa07PgVtkttjvDC8bA1kezhOBKcO0KNzVoDp0ENq7WLxFyLFMQ9USf8LmOY70uV/l8Gpcn1ZT7zRBdEzUUgF/PjZukqVtuHqf9TCO8Ekvjag9XRfVNadKs25rbL60oqpIpEUqAbmQ4j6GFcfBBBPuVlKfidI6O039dAnDUsmeafwCOhEvQmF+N5Diauw3Mk+9TMKNlOWM+pO2DKxX9LLLWGVA9Dqr6dWY0eHjWKUmk2B1h1HYW+aUyoWX2TGsVX9DlNY7CKiQGsL5MRH9IXKMQ8cfMweKoEcwSSXJ
        title: ssh_key_name_that_is_shown_in_gitlab
        can_push: false
```

3. Run `gitlabform my_group`

4. Watch GitLabForm add/reset this deploy key to all projects in "my_group" group in your GitLab!
 
## More complete configuration example

See [config.yml](config.yml) as an example of configuring all projects in "my_group" with some overrides for project "project1".

## More complete usage examples

To apply settings for a single project run:

```gitlabform group/project```

To apply settings for a group of projects run:

```gitlabform group```

To apply settings for all groups of projects defined in the config run:

```gitlabform ALL```

If you are satisfied with results consider running it with cron on a regular basis to ensure that your
GitLab configuration stays the way defined in your config (for example in case of some admin changes
some project settings temporarily by (yuck!) clicking).

## Requirements

* Python 3.5+
* GitLab with API v3 support (< 9.5), tested on 9.1 & 9.3

## Why?

This tool was created as a workaround for missing GitLab features such as [assigning deploy keys per project groups](https://gitlab.com/gitlab-org/gitlab-ce/issues/3890)
but as of now we prefer to use it ever if there are appropriate web UI features, such as [secret variables per project groups](https://gitlab.com/gitlab-org/gitlab-ce/issues/12729) 
(released in GitLab 9.4) to keep configuration as code.

GitLabForm is slightly similar to [GitLab provider](https://www.terraform.io/docs/providers/gitlab/index.html) for Terraform (which we love, btw!),
but it has much more features and uses simpler configuration format.

## How does it work?

It just goes through a loop of projects list and make a series of GitLab API requests.

## Ideas for improvement

* Migrate to GitLab API v4
* Add more features
* Add tests
* Fix bugs

## License

MIT