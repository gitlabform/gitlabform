# Gitlab Configuration

GitlabForm configuration files for https://gitlab.com/gitlabform/gitlabform

Useful to enforce our rules on our Gitlab Group and to test GitlabForm itself in a real environment.

## Running Locally as a test

1. Build the dockerfile as an image `docker build . -f ./Dockerfile -t gitlabform-local`
2. Run the container `docker run gitlabform-local:latest gitlabform --version`
3. Pass the `GITLAB_TOKEN` environment variable: `docker run -it -v $(pwd):/config --env GITLAB_TOKEN= gitlabform-local:latest gitlabform ALL_DEFINED`