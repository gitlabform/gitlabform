from setuptools import setup, find_packages

setup(name='gitlabform',
      version='0.20.0',
      description='Easy configuration as code tool for GitLab using config in plain YAML',
      url='https://github.com/egnyte/gitlabform',
      author='Egnyte',
      keywords=['gitlab', 'configuration-as-code'],
      classifiers=[
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Development Status :: 4 - Beta",
            "Intended Audience :: Information Technology",
            "Intended Audience :: System Administrators",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Topic :: Software Development :: Version Control :: Git",
      ],
      packages=find_packages(),
      install_requires=[
            'requests==2.18.3',
            'pyyaml==3.12',
      ],
      tests_requires=[
            'pytest',
      ],
      scripts=[
            'bin/gitlabform',
      ],
      )
