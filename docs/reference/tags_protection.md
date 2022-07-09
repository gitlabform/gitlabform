# Tags protection

This section purpose is to protect and unprotect the project tags.

It works using the [Protected tags API](https://docs.gitlab.com/ee/api/protected_tags.html#protect-repository-tags) and its syntax is loosely based on it.

The keys are the exact names of the tag or wildcards.

The values are:

* `protected`: `true` or `false`,
* (optional) `create_access_level`: minimal access levels allowed to create (default: `maintainer`, allowed: `no access`, `developer`, `maintainer`)

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    tags:
      "v*":
        protected: true
        create_access_level: developer
      "some-old-tag":
        protected: false
```
