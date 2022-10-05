# Installation

## Run without installing

Note: you **don't** have to install the app to use it.

You can just run the latest stable version with:

* Docker:
```shell
docker run -it -v $(pwd):/config ghcr.io/gitlabform/gitlabform:latest gitlabform
```
* [pipx](https://github.com/pypa/pipx):
```shell
pipx run gitlabform
```


Similarly, you can run the latest 3.* version with:

* Docker:
```shell
docker run -it -v $(pwd):/config ghcr.io/gitlabform/gitlabform:3 gitlabform
```
* [pipx](https://github.com/pypa/pipx):
```shell
pipx run --spec 'gitlabform>=3,<4' gitlabform
```

See [this](https://github.com/gitlabform/gitlabform/pkgs/container/gitlabform) for all the available Docker tags.


## Really install

If you **do** want to install the app you can do it with:

* [pipx](https://github.com/pypa/pipx) (recommended):
```shell
pipx install gitlabform
``` 
* plain `pip`:
```shell
pip3 install gitlabform
```
