# Features

GitLabForm enables you to manage the [(GitLab's) Application Settings](reference/settings.md#application-settings) and:

* Group:
    * [Badges](reference/badges.md#group-badges)
    * [Members (users) {add/remove user, change access level, optional enforce}](reference/members.md#group-members)
    * [Members (groups) {share/unshare with group, change access level, optional enforce}](reference/members.md#group-members)
    * [Members using LDAP Group Links](reference/group_ldap_links.md) (**GitLab Premium (paid) only**)
    * [CI/CD variables](reference/ci_cd_variables.md#group-cicd-variables)
    * [Settings](reference/settings.md#group-settings)
    * [Members using SAML Group Links](reference/group_saml_links.md) (**GitLab Premium (paid) only**)

* Project:
    * [Archive/unarchive](reference/archive_unarchive.md)
    * [Badges](reference/badges.md#project-badges)
    * [CI/CD variables](reference/ci_cd_variables.md#project-cicd-variables)
    * [CI/CD Job Token Scope](reference/job_token_scope.md)
    * [Protected branches](reference/protected_branches.md):
        * access levels (roles) allowed to push/merge/unprotect, allow force push flag,
        * users/groups allowed to push/merge/unprotect, code owner approval required flag (**GitLab Premium (paid) only**),
    * [Protected environments](reference/protected_environments.md)
    * [Deploy keys](reference/deploy_keys.md)
    * [Files {add, edit or delete}, with templating based on Jinja2 (now supports custom variables!)](reference/files.md)
    * [Webhooks](reference/webhooks.md)
    * [Members (users) {add/remove user, change access level, optional enforce}](reference/members.md#project-members)
    * [Members (groups) {share/unshare with group, change access level, optional enforce}](reference/members.md#project-members)
    * [Merge Requests project-level configuration and approval rules](reference/merge_requests.md) (**GitLab Premium (paid) only**)
    * [Pipeline schedules](reference/pipeline_schedules.md)
    * [Push Rules](reference/push_rules.md) (**GitLab Premium (paid) only**)
    * [Integrations](reference/integrations.md)
    * [Settings](reference/settings.md#project-settings)
    * [Tags protect/unprotect](reference/tags_protection.md)
    * [Resource groups](reference/resource_groups.md)
    * [CI/CD Job Token Scope](reference/job_token_scope.md)

...for:

* all projects in your GitLab instance/that you have access to
* a group/subgroup of projects
* a single project

...and a combination of them.
