# Local Development

## Required tools

- Python 3 and Pip 3 for development
- Docker for running Gitlab on local machine
- `jq` used in local environment setup scripts
- [`pre-commit`](https://pre-commit.com/#install) used to run linters and checks prior to commits made locally

## Environment setup

1. Create virtualenv with Python 3, for example in `venv` dir which is in `.gitignore` and activate it:
```
python3 -m venv venv
. venv/bin/activate
```

2. Install GitLabForm in develop mode:
```
pip install -e .
```

Now you can run and debug the app locally.

## Running unit tests

GitLabForm uses `pytest` for tests. You can run unit tests directly on your machine or in a Docker container.

### Running unit tests locally

To run unit tests locally:

1. Activate the virtualenv created above

2. Install the dependencies for tests:
```
pip install -e '.[test]'
```

3. Run `pytest tests/unit` to run all the unit tests.

### Running unit tests in a Docker container

If you have a problem with installing the test dependencies on your localhost, you can run the tests in Docker container
too, like this:

1. Build the image:
```
docker build . -f ./dev/tests.Dockerfile -t gitlabform-tests:latest
```
2. Use it to run the tests:
```
docker run -it -v $(pwd):/code gitlabform-tests:latest /bin/ash -c "cd /code && pytest tests/acceptance"
```

## Running acceptance tests

Most GitLabForm test are the ones that make real operations on a running GitLab instance. You can run them
against a disposable GitLab instance running as a Docker container OR use your own GitLab instance.

### Running acceptance tests using GitLab instance in Docker

1. Run below command to start GitLab in a docker container. Note that it may take a few minutes!

```
./dev/run_gitlab_in_docker.sh
```

2. Run `pytest tests/acceptance` to start all tests.
To run only a single class with tests run f.e.
- `pytest tests/acceptance -k "TestArchiveProject"`.
- `pytest tests/acceptance/<TEST_FILE>.py::<TestClass>::<TEST_METHOD>`

### Acceptance tests for GitLab paid features

To test features that are only available in paid version of Gitlab, you'll need a Gitlab license so that those features are available and the acceptance tests can use it. You can signup for a Gitlab Trial license. Follow the [instructions in Gitlab handbook](https://handbook.gitlab.com/handbook/marketing/developer-relations/contributor-success/community-contributors-workflows/#contributing-to-the-gitlab-enterprise-edition-ee) for details on how to get a license for development purpose. Once you've received a license, take the following step:

1. Copy your license and save it as an `GITLAB_EE_LICENSE` environment variable or in a file named `Gitlab.gitlab-license`. This file is already in `.gitignore`; so it will not be included in your commit.
2. Follow the steps mentioned in previous section.

### Running acceptance tests using your own GitLab instance

**Note**: GitLabForm acceptance tests operate own their own groups, projects and users and it should be safe
to run them on any GitLab instance. However we do not take any responsibility for it. Please review 
the code to ensure what it does and run it at your own risk!

1. Get an admin user API token and put it into `GITLAB_TOKEN` env variable. Do the same with your GitLab instance URL
and put it into `GITLAB_URL` env variable:
```
export GITLAB_URL="https://mygitlab.company.com"
export GITLAB_TOKEN="<my admin user API token>"
```

2. Run `pytest tests/acceptance` to start all tests
To run only a single class with tests run f.e. `pytest tests/acceptance -k "TestArchiveProject"`.

## Preview docs website locally

To make mkdocs build the app website and serve it on your loopback interface do this:
```shell
. venv/bin/activate
pip install -e '.[docs]'
mkdocs serve
```
...and open the provided link (probably [http://127.0.0.1:8000/](http://127.0.0.1:8000/)) in your browser.

## Testing types

Please run `mypy` to test static types:
```shell
mypy .
```
(You may also need to run `mypy --install-types --non-interactive`)

## Code formatting

Please run `black` to format coding style:

```shell
black .
```
