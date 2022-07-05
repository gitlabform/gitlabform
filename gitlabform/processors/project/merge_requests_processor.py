from logging import debug
from cli_ui import debug as verbose

from distutils.version import LooseVersion

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.util.decorators import SafeDict
from gitlabform.processors.util.difference_logger import DifferenceLogger


class MergeRequestsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("merge_requests", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        approvals = configuration.get("merge_requests|approvals")
        if approvals:
            verbose(f"Setting approvals settings: {approvals}")
            self.gitlab.post_approvals_settings(project_and_group, approvals)

        approvers = configuration.get("merge_requests|approvers")
        approver_groups = configuration.get("merge_requests|approver_groups")
        remove_other_approval_rules = configuration.get(
            "merge_requests|remove_other_approval_rules"
        )
        # checking if "is not None" allows configs with empty array to work
        if (
            approvers is not None
            or approver_groups is not None
            and approvals
            and "approvals_before_merge" in approvals
        ):
            verbose(f"Setting approvers...")

            approval_rule_name = "Approvers (configured using GitLabForm)"

            # is a rule already configured and just needs updating?
            approval_rule_id = None
            rules = self.gitlab.get_approvals_rules(project_and_group)
            for rule in rules:
                if rule["name"] == approval_rule_name:
                    approval_rule_id = rule["id"]
                else:
                    if remove_other_approval_rules:
                        debug("Deleting extra approval rule '%s'" % rule["name"])
                        self.gitlab.delete_approvals_rule(project_and_group, rule["id"])

            if not approvers:
                approvers = []
            if not approver_groups:
                approver_groups = []

            if approval_rule_id:
                # the rule exists, needs an update
                verbose(
                    f"Updating approvers rule to users {approvers} and groups {approver_groups}"
                )
                self.gitlab.update_approval_rule(
                    project_and_group,
                    approval_rule_id,
                    approval_rule_name,
                    approvals["approvals_before_merge"],
                    approvers,
                    approver_groups,
                )
            else:
                # the rule does not exist yet, let's create it
                verbose(
                    f"Creating approvers rule to users {approvers} and groups {approver_groups}"
                )
                self.gitlab.create_approval_rule(
                    project_and_group,
                    approval_rule_name,
                    approvals["approvals_before_merge"],
                    approvers,
                    approver_groups,
                )

    def _print_diff(self, project_and_group: str, merge_requests: SafeDict):
        approvals = merge_requests.get("approvals")
        if approvals:
            DifferenceLogger.log_diff(
                "Project %s approvals changes" % project_and_group, dict(), approvals
            )
