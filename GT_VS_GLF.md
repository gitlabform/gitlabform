# GitLab provider for Terraform vs GitLabForm

[Terraform](https://www.terraform.io/), the almost universal "* as code" tool from Hashicorp, which inspired
this app (hence the name!), has a [provider for configuring GitLab](https://www.terraform.io/docs/providers/gitlab/index.html)
using the Hashicorp Configuration Language (HCL).

It is an older and more mature solution than GitLabForm, using a semi-standard configuration language but it's also more
generic. GitLabForm has been built only for managing GitLab and around different concepts that provide a different
set of features, arguably a more powerful one.

**Key differences** between GitLab provider for Terraform ("**GT**") and GitLabForm ("**GLF**"):

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

You can read more about the last two points in the GitLabForm key features design article [here](FEATURES_DESIGN.md).

For your convenience we have prepared a **feature matrix/comparison sheet** for these two tools [here](https://docs.google.com/spreadsheets/d/1CN8rhuK3vBiJ9whhbdVa56pQYKp26-V_s_S7qBtfQRM/edit#gid=0).
Note: this sheet **MAY** contain errors and **WILL** get outdated. Please report these issues in it using comments.
Thank you!
