# Local Development

## Environment setup

1. Create virtualenv with Python 3, for example in `venv` dir which is in `.gitignore` and activate it:
```
virtualenv -p python3 venv
. venv/bin/activate
```

2. Install GitLabForm in develop mode:
```
python setup.py develop
```

Now you can run and debug the app locally.

## Running unit tests

GitLabForm uses py.test for tests. You can run unit tests directly on your machine or in a Docker container.

### Running unit tests locally

To run unit tests locally:

1. Activate the virtualenv created above

2. Install the dependencies for tests:
```
pip install -e .[test]
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

1. (optional) If you have it, put your GitLab license into the `Gitlab.gitlab-license` file. According to the license
agreement (as of now and IANAL) you are allowed to use it for testing and development purposes such as this. This will
make the following script use it to be able to test Premium (paid) features. Of course this license will not leave your
machine.

2. Run below commands to start GitLab in a container. Note that it may take a few minutes!

```
./dev/run_gitlab_in_docker.sh
```

3. Run `pytest tests/acceptance` to start all tests.
To run only a single class with tests run f.e. `py.test tests/acceptance -k "TestArchiveProject"`.

### Running acceptance tests using your own GitLab instance

**Note**: GitLabForm acceptance tests operate own their own groups, projects and users and it should be safe
to run them on any GitLab instance. However we do not take any responsibility for it. Please review 
the code to ensure what it does and run it at your own risk!

1. Get an admin user API token and put it into `GITLAB_TOKEN` env variable. Do the same with your GitLab instance URL
and `GITLAB_URL`:
```
export GITLAB_URL="https://mygitlab.company.com"
export GITLAB_TOKEN="<my admin user API token>"
```

2. Run `pytest tests/acceptance` to start all tests
To run only a single class with tests run f.e. `py.test tests/acceptance -k "TestArchiveProject"`.

## Preview docs website locally

To make mkdocs build the app website and serve it on your loopback interface do this:
```shell
. venv/bin/activate
pip install -e .[docs]
mkdocs serve
```
...and open the provided link (probably [http://127.0.0.1:8000/](http://127.0.0.1:8000/)) in your browser.