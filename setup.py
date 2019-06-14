from setuptools import setup, find_packages
from pypandoc import convert

def convert_markdown_to_rst(file):
      return convert(file, 'rst')


setup(name='gitlabform',
      version=open('version').read(),
      description='Easy configuration as code tool for GitLab using config in plain YAML',
      long_description=convert_markdown_to_rst('README.md'),
      url='https://github.com/egnyte/gitlabform',
      author='Egnyte and GitHub Contributors',
      keywords=['gitlab', 'configuration-as-code'],
      classifiers=[
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Development Status :: 4 - Beta",
            "Intended Audience :: Information Technology",
            "Intended Audience :: System Administrators",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Topic :: Software Development :: Version Control :: Git",
      ],
      packages=find_packages(),
      install_requires=[
            'requests>=2.20.0',
            'pyyaml>=4.2b1',
            'Jinja2>=2.10.1,<3',
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
