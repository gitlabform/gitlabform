# Coding guidelines

Please do:

* use the common sense,
* add tests along with the new code that prove that it works:
    * when adding/changing non-trivial logic please add unit tests,
    * for all bug fixes and new features using GitLab API please add acceptance tests
* use [Black](https://github.com/psf/black) code formatter:
```
black .
```
We recommend and provide a config for [pre-commit](https://pre-commit.com) to generate a pre-commit hook that will automatically reformat your contributions with Black.
* squash your commits (unless there is a reason not to),
* try to write [good commit message(s)](https://chris.beams.io/posts/git-commit/),

...and so on.

Additionally, please follow these GitLabForm-specific guidelines:

* do not uptick `version` file in your PR - you will quickly have to resolve conflicts if you do that as we release more often than the usual baking time of a PR...

We are open to refactoring but in case of bigger efforts we suggest creating an issue first and discussing what you propose to do before doing it.
