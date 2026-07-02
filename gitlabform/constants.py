# f.e. bad syntax in the config file ~= "it's your fault" 😅
EXIT_INVALID_INPUT = 1
# f.e. when requests to GitLab fail ~= "it's not your fault" 😎
EXIT_PROCESSING_ERROR = 2

# legacy single approval rule name
APPROVAL_RULE_NAME = "Approvers (configured using GitLabForm)"

# ------ Logging constants for custom log levels -----
# Log out Diff logs higher than WARNING (i.e. not requiring --verbose too) but without having to masquerade as an
# error/unexpected by using logger.warning/error etc
DIFF_LOG_LEVEL = 32
# Log out notices about number of failed projects etc
NOTICE_LOG_LEVEL = 33
