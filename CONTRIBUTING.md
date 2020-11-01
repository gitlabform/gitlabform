# Contributing guide

All contributions are welcome!

You can:
* ask questions, report issues, ask for features or write anything message to the app authors - use **Issues** for all
of these,
* contribute to the documentation and example configuration - with **Pull Requests**, 
* contribute your bug fixes, new features, refactoring and other code improvements - with **Pull Requests**,

...and probably more! If you want to help in any way but don't know how - create an **Issue**.

## Issues

As the project is not (yet ;) flooded with issues the guidelines for creating them are not very strict
and should be very common sense ones.

### Questions

Before asking a question please make sure that you have read the docs, especially the example 
[config.yml](https://github.com/egnyte/gitlabform/blob/master/config.yml).  


### Problems

Before reporting a problem please update GitLabForm to the latest version and check if the issue persists.

If it does then please try to report what environment you have, what you try to do, what you expect to happen
and what does in fact happen.

To be more specific please remember to:
* provide GitLab version,
* provide GitLabForm version,
* provide your Python version and Operating System,
* provide config in whole, or a relevant fragment (of course you can and should redact any values you need
to redact for privacy and security reasons),

### Feature requests

Please note that although we do accept feature requests we do not promise to fulfill them.

However, it's still worth creating an issue for this as it shows interest in given feature and that may be taken
into account by both existing app authors and new contributors when planning to implement something new.

## Pull Requests

### Documentation

Just use the common sense:

* try to use similar style as existing docs,
* use tools to minimize spelling and grammar mistakes,

..and so on.

### Code improvements

#### Development environment setup how-to

1. Create virtualenv with Python 3.5+, for example in `venv` dir which is in `.gitignore` and activate it:
```
virtualenv -p python3 venv
. venv/bin/activate
```

2. Install build requirements - `pandoc` binary package + `pypandoc` python package:
```
# for macOS:
brew install pandoc  
pip3 install pypandoc
```

3. Install GitLabForm in develop mode:
```
python setup.py develop
```

#### How to implement things in GitLabForm?

Please see the [implementation design article](docs/IMPLEMENTATION_DESIGN.md).

#### Running unit tests locally

GitLabForm uses py.test for tests. To run unit tests locally:

1. Activate the virtualenv created above

2. `pip install pytest`

3. Run `py.test --ignore gitlabform/gitlabform/test` to run all tests except the integration tests (see below).

#### Running integrations tests locally or on own GitLab instance

GitLabForm also comes with a set of tests that make real requests to a running GitLab instance. You can run them
against a disposable GitLab instance running as a Docker container OR use your own GitLab instance.

##### Running integration tests using GitLab instance in Docker

1. Run below commands to start GitLab in a container. Note that it may take a few minutes!

```
./dev/run_gitlab_in_docker.sh
export GITLAB_URL=$(cat gitlab_url.txt)
export GITLAB_TOKEN=$(cat gitlab_token.txt)
```

2. Run `py.test gitlabform/gitlabform/test` to start the tests

##### Running integration tests using your own GitLab instance

**Note**: although GitLabForm integration tests operate own their own groups, projects and users, it should be safe
to run them against your own GitLab instance, but we DO NOT take any format responsibility for it. Please review 
the code to ensure what it does and run it at your own risk!

1. Get an admin user API token and put it into `GITLAB_TOKEN` env variable. Do the same with your GitLab instance URL
and `GITLAB_URL`:
```
export GITLAB_URL="https://mygitlab.company.com"
export GITLAB_TOKEN="<my admin user API token>"
```

2. Run `py.test gitlabform/gitlabform/test` to start the tests

#### General coding guidelines

Similarly to the guidelines for making PRs with documentation improvements - please use the common sense:

* add tests along with the new code that prove that it works:
  * in case of non-trivial logic add/change please add unit tests,
  * for all bug fixes and new features using GitLab API please add integration tests
* use [Black](https://github.com/psf/black) code formatter,
* squash your commits (unless there is a reason not to),
* try to write [good commit message(s)](https://chris.beams.io/posts/git-commit/),
 
...and so on.

Additionally please follow these GitLabForm-specific guidelines:
* do not uptick `version` file in your PR - you will quickly have to resolve conflicts if you do that as we release more often than the usual baking time of a PR...

We are open to refactoring but in case of bigger efforts we suggest creating an issue first and discussing
what you propose to do before doing it.
