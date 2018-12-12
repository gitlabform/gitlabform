from gitlabform.gitlab.core import GitLabCore
import time as t
from datetime import *


class GitLabPipelines(GitLabCore):
    def check_envs_and_retry(self, sddc_envs_id, branches):
        print('Checking ENVS & retry if failed')
        for i in range(3):
            sleep = 10
            print('Current time %s, waiting %ss.' % (datetime.now(), sleep))
            t.sleep(sleep)
            print('Starts at %s.' % (datetime.now()))
            for branch in branches:
                pipelines = self._make_requests_to_api("projects/%s/pipelines?ref=%s", (sddc_envs_id, branch))
                last_pipeline = pipelines[0]
                if last_pipeline['status'] == 'failed' or last_pipeline['status'] == 'pending':
                    print('Branch: %s - status: %s, id: %s\nweb_url: %s' %
                          (branch, last_pipeline['status'], last_pipeline['id'], last_pipeline['web_url']))
                    retry_pipeline = self._make_requests_to_api("projects/%s/pipelines/%s/retry",
                                                               (sddc_envs_id, last_pipeline['id']),
                                                               method='POST',expected_codes=[200, 201])

