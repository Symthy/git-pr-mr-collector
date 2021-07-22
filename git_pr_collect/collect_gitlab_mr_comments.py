import configparser
from typing import List, Optional

import requests

from utils.api_executer import execute_get_api, retry_execute_git_api
from utils.pr_domain import PullRequestDataList, PullRequestReviewCommentList

CONF_DIR_PATH = './conf/'
GITLAB_TOKEN_FILE_PATH = CONF_DIR_PATH + 'gitlab_access_token'
COLLECT_TARGET_PROJECT_CONF_PATH = CONF_DIR_PATH + 'target_gitlab_project.conf'

MERGE_REQUEST_LIST_FILE_NAME = 'mr_list'
OUTPUT_DIR_PATH = 'out/gitlab'


def main():
    def build_request_header():
        with open(GITLAB_TOKEN_FILE_PATH) as f:
            gitlab_access_token = f.read()
        return {
            'Authorization': 'Bearer ' + gitlab_access_token
        }

    def build_get_gitlab_projects(host: str) -> str:
        return 'https://' + host + '/api/v4/projects'

    def build_collect_gitlab_merge_requests_api_url(page_count, author: Optional[str]) -> str:
        return 'https://' + GITLAB_HOST + '/api/v4/projects/' + PROJECT_ID + '/merge_requests?per_page=100&page=' + page_count

    def build_collect_gitlab_mr_comments_api_url(page_count, merge_request_iid: str):
        return 'https://' + GITLAB_HOST + '/api/v4/projects/' + PROJECT_ID + '/merge_requests/' + merge_request_iid + '/notes?per_page=100&page=' + page_count

    def execute_gitlab_api(url: str) -> List:
        headers = build_request_header()
        response = requests.get(url, headers=headers)
        print(response.status_code, response.reason, url)
        if response.status_code == 200:
            return response.json()
        return []

    # Callback-only function used by retry_execute_github_api()
    def collect_and_write_merge_requests(page_count: int, non_arg) -> int:
        api_url = build_collect_gitlab_merge_requests_api_url(page_count)
        response_json_pr_array = execute_get_api(api_url, build_request_header())
        pr_data_list = PullRequestDataList.github_pr(response_json_pr_array)
        pr_data_list.write_csv(OUTPUT_DIR_PATH, MERGE_REQUEST_LIST_FILE_NAME)
        # get review comment in PR
        for pr_data in pr_data_list.values:
            retry_execute_git_api(collect_and_write_mr_comments, pr_data)
        return len(response_json_pr_array)

    # Callback-only function used by retry_execute_github_api()
    def collect_and_write_mr_comments(page_count: int, pr_data: PullRequestDataList.PullRequestData) -> int:
        api_url = build_collect_gitlab_mr_comments_api_url(page_count, pr_data.pr_num)
        response_json_review_comments_array = execute_get_api(api_url, build_request_header())
        pr_review_comment_list = PullRequestReviewCommentList.gitlab_mr(response_json_review_comments_array, pr_data)
        pr_name = pr_data.build_pr_name()
        pr_review_comment_list.write_csv(OUTPUT_DIR_PATH, pr_name)
        pr_review_comment_list.write_md(OUTPUT_DIR_PATH, pr_name)
        return len(response_json_review_comments_array)

    conf = configparser.ConfigParser()
    conf.read(COLLECT_TARGET_PROJECT_CONF_PATH)
    GITLAB_HOST = conf.get('DEFAULT', 'GITLAB_HOST')
    target_project_name = conf.get('DEFAULT', 'PROJECT_NAME')
    projects: List = list(filter(lambda pj: pj['name'] == target_project_name,
                                 execute_gitlab_api(build_get_gitlab_projects(GITLAB_HOST))))
    if len(projects) == 0:
        print('No specified gitlab project')
        return
    PROJECT_ID = projects[0]['id']
    retry_execute_git_api(collect_and_write_merge_requests)
