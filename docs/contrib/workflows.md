# GitHub Workflows

We trigger acceptance tests on GitHub Actions against "Self-hosted" images of GitLab with temporary licenses granted to 
us by GitLab's customer success team.

These tests are run in an GitHub Environment, requiring approval from a maintainer, and the licenses assigned to this
project's maintainers are stored as GitHub Repository Secrets to prevent misuse.

## Pipeline Trigger 
We use `pull_request_target` as the event to trigger PR pipelines on Forks- which has a downside that we can't test 
pipeline changes submitted from forks until merged into main, but allows us to pass License Secrets to Forks more easily.

We use `pull_request` as the event to trigger PR pipelines on the main repository, which allows us to test pipeline 
changes submitted before merging into main, with a Branch Protection rule in place to lock branch pushes to maintainers
only on the main repository.

## License management

Requesting new Premium/Ultimate Licenses is done via GitLab's Contribution to EE process [here](https://handbook.gitlab.com/handbook/marketing/developer-relations/contributor-success/community-contributors-workflows/#contributing-to-the-gitlab-enterprise-edition-ee).

As a Maintainer, when you receive a new license key, please add/update it to the GitHub Repository Secrets.