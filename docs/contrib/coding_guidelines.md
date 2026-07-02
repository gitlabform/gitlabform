# Coding guidelines

Please do:

* use the common sense,
* add tests along with the new code that prove that it works:
    * when adding/changing non-trivial logic please add unit tests,
    * for all bug fixes and new features using GitLab API please add acceptance tests
* use info as the base log level, debug if you might expose sensitive information (such as raw API request/responses)
    * by default we log out WARNING and above issues, with INFO logged out when specifying the `--verbose` argument in CLI 
    * use `logging` module for logging, do not use `print` statements
    * we have a custom log level for "diff" messages, used only in the difference_logger
    * we have a custom log level "notice" used only in gitlabfor __init__.py in order to output version information and the total numbers of Projects/Groups processed
* add or update the docs for new features,
* use [pre-commit](https://pre-commit.com) to automatically reformat your code and run linters before committing,
* squash your commits (unless there is a reason not to),
* follow [conventional-commit format](https://www.conventionalcommits.org/en/v1.0.0/#summary) in order to produce consistent human and machine-readable commit messages, making it easier for maintainers to produce the CHANGELOG.

We are very open to refactoring but in case of bigger efforts we suggest creating an issue first and discussing what you propose to do before doing it.
