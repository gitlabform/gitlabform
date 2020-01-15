import os
import logging
import sys

import yaml
from pathlib import Path


class ConfigurationCore:

    config = None
    config_dir = None

    def __init__(self, config_path=None, config_string=None):

        if config_path and config_string:
            logging.fatal('Please initialize with either config_path or config_string, not both.')
            sys.exit(1)

        try:
            if config_path:
                # using this env var should be considered unofficial, we need this temporarily
                # for backwards compatibility. support for it may be removed without notice, do not use it!
                if 'APP_HOME' in os.environ:
                    config_path = os.path.join(os.environ['APP_HOME'], 'config.yml')
                # this case is only meant for using gitlabform as a library
                elif not config_path:
                    config_path = os.path.join(str(Path.home()), '.gitlabform', 'config.yml')
                elif config_path in [os.path.join('.', 'config.yml'), 'config.yml']:
                    config_path = os.path.join(os.getcwd(), 'config.yml')

                logging.info("Reading config from file: {}".format(config_path))

                with open(config_path, 'r') as ymlfile:
                    self.config = yaml.safe_load(ymlfile)

                # we need config path for accessing files for relative paths
                self.config_dir = os.path.dirname(config_path)
            else:
                logging.info("Reading config from provided string.")
                self.config = yaml.safe_load(config_string)
                self.config_dir = '.'

        except (FileNotFoundError, IOError):
            raise ConfigFileNotFoundException(config_path)

        except Exception:
            if config_path:
                raise ConfigInvalidException(config_path)
            else:
                raise ConfigInvalidException(config_string)

    def get(self, path, default=None):
        """
        :param path: "path" to given element in YAML file, for example for:

        group_settings:
          sddc:
            deploy_keys:
              qa_puppet:
                key: some key...
                title: some title...
                can_push: false

        ..a path to a single element array ['qa_puppet'] will be: "group_settings|sddc|deploy_keys".

        To get the dict under it use: get("group_settings|sddc|deploy_keys")

        :return: element from YAML file (dict, array, string...)
        """
        tokens = path.split('|')
        current = self.config

        try:
            for token in tokens:
                current = current[token]
        except:
            if default is not None:
                return default
            else:
                raise KeyNotFoundException

        return current


class ConfigFileNotFoundException(Exception):
    pass


class ConfigInvalidException(Exception):
    pass


class KeyNotFoundException(Exception):
    pass
