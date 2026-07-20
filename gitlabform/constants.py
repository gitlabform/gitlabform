# f.e. bad syntax in the config file ~= "it's your fault" 😅
EXIT_INVALID_INPUT = 1
# f.e. when requests to GitLab fail ~= "it's not your fault" 😎
EXIT_PROCESSING_ERROR = 2

# legacy single approval rule name
APPROVAL_RULE_NAME = "Approvers (configured using GitLabForm)"

# ------ Logging constants for custom log levels -----
# Why these numbers? https://docs.python.org/3/howto/logging.html#logging-levels
# Anything in the 30-40 range will be logged out when the log level is set to WARNING -> we use WARNING as our
# default level, unless --verbose is supplied at which point INFO level is set
# Log out Diff logs without requiring --verbose
DIFF_LOG_LEVEL = 32
# Log out notices about number of failed and successful projects, and processing completed etc. from __init__.py
NOTICE_LOG_LEVEL = 33
