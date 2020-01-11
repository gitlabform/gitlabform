# Hierarchical, merged and overridable configuration

GitLabForm has been heavily inspired by [Puppet's hiera](https://puppet.com/docs/puppet/latest/hiera_intro.html). This
is where we borrowed from the concept of a hierarchical configuration that is inherited from the higher to the lower
levers while you also can override some config parts on the lower levels.

**Example 1 - configuration inheritance & overriding **

You want to configure all your GitLab instance projects to have JIRA integration enabled for your MRs to have
ticket ids shown as links to JIRA in the web UI, but you DON'T want the integration that enables to close JIRA
tickets from MRs that have "closes <ticket_id>" in their description, so you do this:
```yaml
common_settings:
  # common settings for ALL projects in ALL groups
  services:
    jira:
      url: https://jira.yourcompany.com
      commit_events: false
      merge_requests_events: true 
      username: fake # this field is required by the GitLab API, but you can set it to any value
      password: fake # this field is required by the GitLab API, but you can set it to any value
``` 
...but you DO want this feature for a group of projects, but without comments about each commit added to JIRA,
so then you add this to your config:
```yaml
group_settings:
  # settings for ALL projects in 'some_group_name' group
  some_group_name:
    services:
      jira:
        username: real_username
        password: real_password
        jira_issue_transition_id: 123

 ```
...and finally you realize that for a single project in that group you also DO WANT those comments (for example for
compliance reasons), so you add:
```yaml
project_settings:
  # settings for a single project
  some_group_name/specific_project_name:
    services:
      jira:
        commit_events: true
 ```

Note how you don't have to provide a full config each time - only the parts that are changing. This is because the configs
from the higher level are being merged with the ones on the lower.

**Example 2 - adding elements**

You want to add a default README file to all your projects that contains a convenience link to search for given project
in Confluence. So you add this to your config:

```yaml
common_settings:
  files:
    "README.md":
      overwrite: false  # do not overwrite if someone already added a real README
      only_first_branch: true  # add the file only to the first branch in the below list 
      branches:
        - develop
        - master
      skip_ci: true  # this will prevent the commit that applies this file change triggering CI build
      content: |
        This is a default project README. Please replace it with a proper one!
        Search for this project in Confluence with this [link](https://confluence.yourcompany.com/dosearchsite.action?cql=siteSearch%20~%20%22{{ project }}%22&includeArchivedSpaces=false).
```

Then you realize that for "app_1" group projects you also want to add a default `.gitignore` file, so you add this to your config:

```yaml
group_settings:
  app_1:
    files:
      ".gitignore":
        overwrite: false
        only_first_branch: true 
        branches:
          - develop
          - master
        skip_ci: true
        content: |
          *.swp
          *.bak
```

Note that the projects in the group "app_1" will have BOTH files added - `README.md` and `.gitignore`. This is because
the configs are additive for most "listed" elements.

(Note that you can disable addivity selectively by using `skip: true` configuration expression, like this:

```yaml
project_settings:
  app_1/some_repo:
    files:
      ".gitignore":
        skip: true  # thanks to this `app_1/some_repo` will NOT get `.gitignore` file from GitLabForm
```
)

# Raw parameters passing

When GitLabForm was originally developed, in 2017, GitLab development pace was so fast that we were not able to keep up with it
by updating GitLabForm whenever a parameter was added or changed in the GitLab's API.

Because of that we made a decision to use "raw parameters passing" - for many configuration elements whatever you put inside
it as a dict, will be sent with a PUT/POST request into the appropriate GitLab API as-is.

The advantage of this approach is that you can use each of the +40 parameters from [the GitLab API for Projects](https://docs.gitlab.com/ee/api/projects.html#edit-project)
to configure your project with GitLabForm and when GitLab adds a new parameter there you can start using it on the day
you update your GitLab instance, without waiting for GitLabForm to be updated to support it.

The disadvantage is that you may also be hit by GitLab API changes (that you have have missed in its changelog) and/or
GitLab bugs that may render parts of your config not working after you update your GitLab instance.

But note that in this case you can often fix the problem on your own by for example changing the deprecated names
of your parameters in your config to new ones without waiting for a GitLabForm update.  
