from setuptools import setup, find_packages
from pypandoc import convert_file

def convert_markdown_to_rst(file):
      return convert_file(file, 'rst')


setup(name='gitlabform',
      version=open('version').read(),
      description='Specialized "configuration as a code" tool for GitLab projects, groups and more'
                  ' using hierarchical configuration written in YAML',
      long_description=convert_markdown_to_rst('README.md'),
      url='https://github.com/egnyte/gitlabform',
      author='Egnyte and GitHub Contributors',
      keywords=['gitlab', 'configuration-as-code'],
      classifiers=[
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Information Technology",
            "Intended Audience :: System Administrators",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Topic :: Software Development :: Version Control :: Git",
      ],
      packages=find_packages(),
      install_requires=[
            'certifi', # we want to keep the certs latest
            'altgraph==0.16.1',
            'atomicwrites==1.3.0',
            'attrs==19.1.0',
            'bandit==1.6.2',
            'chardet==3.0.4',
            'coverage==5.0.1',
            'coverage-badge==1.0.1',
            'decorator==4.4.0',
            'deepdiff==4.0.9',
            'gitdb2==2.0.6',
            'GitPython==3.0.5',
            'idna==2.8',
            'importlib-metadata==0.21',
            'Jinja2==2.10.1',
            'jsonpickle==1.2',
            'macholib==1.11',
            'MarkupSafe==1.1.1',
            'more-itertools==7.2.0',
            'ordered-set==3.1.1',
            'packaging==19.1',
            'pbr==5.4.4',
            'pluggy==0.13.0',
            'py==1.8.0',
            'PyInstaller==3.5',
            'pyparsing==2.4.2',
            'pytest==5.1.2',
            'pytest-cov==2.8.1',
            'PyYAML==5.1.2',
            'requests==2.22.0',
            'six==1.12.0',
            'smmap2==2.0.5',
            'stevedore==1.31.0',
            'urllib3==1.25.3',
            'wcwidth==0.1.7',
            'zipp==0.6.0',
      ],
      tests_require=[
            'pytest',
      ],
      setup_requires=[
            'pypandoc',
      ],
      scripts=[
            'bin/gitlabform',
      ],
      )
