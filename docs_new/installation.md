# Requirements and Installation

## Requirements

* Docker or Python 3.6-3.10
* GitLab 11+
* GitLab Premium (paid) for some features

## Installation

Run the latest stable version with:

* Docker:
```shell
docker run -it -v $(pwd):/config ghcr.io/gdubicki/gitlabform:latest gitlabform
```
* [pipx](https://github.com/pypa/pipx):
```shell
pipx run gitlabform
```

Run the latest 2.* version with:

* Docker:
```shell
docker run -it -v $(pwd):/config ghcr.io/gdubicki/gitlabform:2 gitlabform
```
* [pipx](https://github.com/pypa/pipx):
```shell
pipx run --spec 'gitlabform>=2,<3' gitlabform
```

See [this](https://github.com/gdubicki/gitlabform/pkgs/container/gitlabform) for all the available Docker tags.


Install with:

* [pipx](https://github.com/pypa/pipx) (recommended):
```shell
pipx install gitlabform
``` 
* plain `pip`:
```shell
pip3 install gitlabform
```
