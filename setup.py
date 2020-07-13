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
            'certifi',  # we want the latest root certs for security
            'requests==2.24.0',
            'chardet==3.0.4',
            'idna==2.10',
            'Jinja2==2.11.2',
            'MarkupSafe==1.1.1',
            'PyYAML==5.3.1',
            'urllib3==1.25.9',
            'luddite==1.0.1',
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
