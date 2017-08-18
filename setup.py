from setuptools import setup, find_packages

setup(name='gitlabform',
      version='0.16.8',
      description='Easy configuration as code tool for GitLab using config in plain YAML',
      url='https://github.com/egnyte/gitlabform',
      author='Egnyte',
      packages=find_packages(),
      install_requires=[
            'requests==2.18.3',
            'pyyaml==3.12',
      ],
      scripts=[
            'bin/gitlabform',
      ],
      )
