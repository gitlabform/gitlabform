# Contributing guide

All contributions are welcome!

You can:
* ask questions, report issues, ask for features or write anything message to the app authors - use **Issues** for all
of these,
* contribute to the documentation and example configuration - with **Pull Requests**, 
* contribute your bugfixes, new features, refactoring and other code improvements - with **Pull Requests**,

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
  * provide config in whole or a relevant fragment (of course you can and should redacting any values you need
to redact for privacy and security reasons),

### Feature requests

Please note that although we do accept feature requests we do not promise to fulfill them.

But it's still worth creating an issue for this as it shows interest in given feature and that may be taken
into account by both existing app authors as well as new contributors when planning to implement something
new.

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

3. Install gitlabform in develop mode:
```
python setup.py develop
```

#### General guidelines

Similarly to the guidelines for making PRs with documentation improvements - please use the common sense:

* add tests along with the new code that prove that it works:
  * in case of non-trivial logic add/change please add unit tests,
  * for all bug fixes and new features using GitLab API please add integration tests
   (after [#75](https://github.com/egnyte/gitlabform/pull/75) gets merged),
* follow the standard Python coding guidelines ([PEP8](https://www.python.org/dev/peps/pep-0008/),
* try to use similar style and formatting of the code as existing one,
* squash your commits (unless there is a reason not to),
* try to write [good commit message(s)](https://chris.beams.io/posts/git-commit/),
 
..and so on.

We are open to refactoring but in case of bigger efforts we suggest creating an issue first and discussing
what you propose to do before doing it.

#### How to implement things in GitLabForm?

Please see the [implementation design article](IMPLEMENTATION_DESIGN.md).
