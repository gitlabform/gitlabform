import codecs
import os

from setuptools import setup, find_packages

with codecs.open("README.md", encoding="utf-8") as f:
    README = f.read()


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
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/egnyte/gitlabform",
    author="Egnyte and GitHub Contributors",
    keywords=["gitlab", "configuration-as-code"],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
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
    install_requires=[
        "certifi",  # we want the latest root certs for security
        "requests==2.26.0",
        "Jinja2==2.11.3",
        "MarkupSafe==1.1.1",
        "PyYAML==5.4.1",
        "luddite==1.0.2",
        "cli-ui==0.14.1",
        "packaging==21.0",
        "mergedeep==1.3.4",
    ],
    extras_require={
        "test": [
            "pytest==6.2.4",
            "xkcdpass==1.19.2",
            "pre-commit==2.13.0",  # not really for tests, but for development
            "coverage==5.5",
            "pytest-cov==2.12.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "gitlabform=gitlabform.run:run",
        ],
    },
)
