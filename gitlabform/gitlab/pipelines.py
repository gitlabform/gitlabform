from gitlabform.gitlab.core import GitLabCore
import time as t
from datetime import *


class GitLabPipelines(GitLabCore):
    SDDC_ENVS = 'sddc/envs'
    BRANCHES = ['egnyte', 'global_production', 'global_qa', 'internal', 'partners', 'perf2', 'production',
                    'qa', 'qabranchprod', 'qabranchrc']

    def check_envs(self):
        sleep = 60
        print('Current time %s, waiting %ss.' % (datetime.now(), sleep))
        t.sleep(sleep)
        print('Starts at %s.' % (datetime.now()))
        for branch in self.BRANCHES:
            pipelines = self._make_requests_to_api("projects/%s/pipelines?ref=%s", (self.SDDC_ENVS, branch))
            last_pipeline = pipelines[0]
            if last_pipeline['status'] == 'failed' or last_pipeline['status'] == 'pending':
                print('Branch: %s - status: %s, id: %s\nweb_url: %s' %
                      (branch, last_pipeline['status'], last_pipeline['id'], last_pipeline['web_url']))
                retry_pipeline = self._make_requests_to_api("projects/%s/pipelines/%s/retry", (env, last_pipeline['id']),
                                                           method='POST',expected_codes=[200, 201])
                print(retry_pipeline)