# Similar apps

## GitLab provider for Terraform

[Terraform](https://www.terraform.io/), the almost universal "* as a code" tool from Hashicorp, which inspired
this app (hence the name!), has a [provider for configuring GitLab](https://www.terraform.io/docs/providers/gitlab/index.html)
using the Hashicorp Configuration Language (HCL).

It is an older and more mature solution than GitLabForm, using a de-facto standard configuration language, but it's also more
generic.

GitLabForm has been built specifically for managing GitLab and has been designed around different concepts that provide a different set of features, arguably a more powerful one.

### Key differences

...between GitLab provider for Terraform ("**GT**") and GitLabForm ("**GLF**"):

* **GT** allows creating resources such as users, groups and projects while **GLF** (as of now) allows only configuring existing
  entities (with an exception for management of files in the repo, which is a unique **GLF** feature),

* **GT** can only manage specific groups and projects. **GLF** allows configuring everything it supports for ALL of your projects
  in your GitLab instance (with the possibility to provide more specialized configuration for some of the groups and projects).

* **GT** is using a structured language which describes each managed resource explicitly (with iterators, of course) while
  **GLF** is based on YAML and a concept of hierarchical, inheritable configuration with merging/overwriting and addivity.
  Therefore only with **GLF** you can write configs like "For all projects in group X do this, but for specific projects X/A
  and X/B in it also do this and for X/C do something a bit different".

* **GT** wraps the GitLab API into abstractions while **GLF** in many cases (explained in the docs) makes PUT/POST requests of the dicts found
  in the config as-is to the GitLab API. **GT** approach is more convenient and less "raw" (you read **GT** docs when using it, while
  for **GLF** you also have to read GitLab API docs) but **GLF** allows you to use all of the GitLab API features - **GT** supports only
  a fraction of GitLab's API parameters for editing group and project while **GLF** by design allows you to use all of them.
  Also when you update your GitLab instance you can start using new API features immediately with **GLF** while with **GT** you
  have to wait until its new version supporting those features is released.

### Feature matrix/comparison sheet

For your convenience we have prepared [GitLab provider for Terraform vs GitLabForm feature matrix / comparion sheet](https://docs.google.com/spreadsheets/d/1RenC5OoLW_bt8QYrijNP42w8SGBw8JTg1-7RKWgStrQ/edit?usp=sharing).
Note: this sheet **MAY** contain errors and **WILL** get outdated. Please report these issues in it using comments.
Thank you!

## GitLab Configuration as Code (GCasC)

Since [v3.10.0](https://github.com/gitlabform/gitlabform/releases/tag/v3.10.0) you can configure the GitLab's application settings too with GitLabForm.

For possibly more instance-wide settings of GitLab (like appearance, features, license, etc.) you can also check out
the [GitLab Configuration as Code (GCasC)](https://github.com/Roche/gitlab-configuration-as-code) project.

(Although as of May 2024 it looks a bit stale.)
