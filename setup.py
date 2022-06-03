import codecs
import os
import re
from setuptools import setup, find_packages

with codecs.open("README.md", encoding="utf-8") as f:
    readme = f.read()

# ToC doesn't work when viewed in PyPI :(
# it also contains link to changelog which for PyPI is added to the end of the readme
# so let's remove the ToC here
regexp = re.compile(r"## Table of Contents(.*)## Features", re.MULTILINE + re.DOTALL)
readme = re.sub(regexp, "## Features", readme)

with codecs.open("CHANGELOG.md", encoding="utf-8") as f:
    changelog = f.read()

long_description = readme + "\n" + changelog


def get_version_file_path():
    github_actions_path = "/home/runner/work/gitlabform/gitlabform"
    if os.path.isfile(github_actions_path + "/version"):
        return github_actions_path + "/version"
    else:
        return "version"


setup(
    name="gitlabform",
    version=open(get_version_file_path()).read(),
    description='Specialized "configuration as a code" tool for GitLab projects, groups and more'
    " using hierarchical configuration written in YAML",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gitlabform/gitlabform",
    author="Greg Dubicki and Contributors",
    keywords=["gitlab", "configuration-as-code"],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    packages=find_packages(),
    package_data={"": ["LICENSE", "version", "*.md", "config.yml"]},
    include_package_data=True,
    install_requires=[
        "certifi",  # we want the latest root certs for security
        "requests==2.27.1",
        "Jinja2==2.11.3",
        "MarkupSafe==1.1.1",
        "ruamel.yaml==0.17.17",
        "luddite==1.0.2",
        "cli-ui==0.15.2",
        "packaging==21.3",
        "mergedeep==1.3.4",
        "yamlpath==3.6.4",
        "ez-yaml==1.2.0",
    ],
    extras_require={
        "test": [
            "pytest==7.0.1",
            "xkcdpass==1.19.3",
            "pre-commit==2.17.0",  # not really for tests, but for development
            "coverage==6.4.1",
            "pytest-cov==3.0.0",
            "deepdiff==5.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gitlabform=gitlabform.run:run",
        ],
    },
)
