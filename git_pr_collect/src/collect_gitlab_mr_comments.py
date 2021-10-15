import configparser
from typing import List, Optional

from api.api_executer import execute_get_api, retry_execute_git_api
from domain.pull_request import PullRequestDataList
from domain.pull_request_review_comment import PullRequestReviewCommentList
from exception.error import NonExistTargetError

CONF_DIR_PATH = './conf/'
GITLAB_TOKEN_FILE_PATH = CONF_DIR_PATH + 'gitlab_access_token'
COLLECT_TARGET_PROJECT_CONF_PATH = CONF_DIR_PATH + 'target_gitlab_project.conf'

MERGE_REQUEST_LIST_FILE_NAME = 'mr_list'
OUTPUT_DIR_PATH = 'out/gitlab'

GITLAB_BASEURL = 'https://{GITLAB_HOST}/api/v4'
GITLAB_GET_PROJECTS_URL = GITLAB_BASEURL + '/projects'
GITLAB_GET_MR_URL = GITLAB_GET_PROJECTS_URL + '/{PROJECT_NAME}/merge_requests'


def build_request_header():
    with open(GITLAB_TOKEN_FILE_PATH) as f:
        gitlab_access_token = f.read()
    return {
        'Authorization': 'Bearer ' + gitlab_access_token
    }


def build_get_merge_request_api_base_url(project_name: str = "") -> str:
    conf = configparser.ConfigParser()
    conf.read(COLLECT_TARGET_PROJECT_CONF_PATH)
    gitlab_host = conf.get('DEFAULT', 'GITLAB_HOST')
    target_project_name = conf.get('DEFAULT', 'PROJECT_NAME') if project_name == "" else project_name
    mr_api_url = GITLAB_GET_MR_URL.replace('{GITLAB_HOST}', gitlab_host).replace('{PROJECT_NAME}', target_project_name)
    return mr_api_url


def build_get_gitlab_projects(gitlab_host: str) -> str:
    return GITLAB_GET_PROJECTS_URL.replace('{GITLAB_HOST}', gitlab_host)


def build_collect_gitlab_merge_requests_api_url(page_count, author: Optional[str]) -> str:
    return build_get_merge_request_api_base_url() + '?per_page=100&page=' + page_count


def build_collect_gitlab_mr_comments_api_url(page_count, merge_request_iid: str):
    return build_get_merge_request_api_base_url() + merge_request_iid + '/notes?per_page=100&page=' + page_count


# Callback-only function used by retry_execute_git_api()
def collect_and_write_merge_requests(page_count: int, non_arg) -> int:
    api_url = build_collect_gitlab_merge_requests_api_url(page_count)
    response_json_pr_array = execute_get_api(api_url, build_request_header())
    pr_data_list = PullRequestDataList.create_from_github_pr(response_json_pr_array)
    pr_data_list.write_csv(OUTPUT_DIR_PATH, MERGE_REQUEST_LIST_FILE_NAME)
    # get review comment in PR
    for pr_data in pr_data_list.values:
        retry_execute_git_api(collect_and_write_mr_comments, pr_data)
    return len(response_json_pr_array)


# Callback-only function used by retry_execute_git_api()
def collect_and_write_mr_comments(page_count: int, pr_data: PullRequestDataList.PullRequestData) -> int:
    api_url = build_collect_gitlab_mr_comments_api_url(page_count, pr_data.pr_num)
    response_json_review_comments_array = execute_get_api(api_url, build_request_header())
    pr_review_comment_list = PullRequestReviewCommentList.gitlab_mr(response_json_review_comments_array, pr_data)
    pr_name = pr_data.build_pr_name()
    pr_review_comment_list.write_csv(OUTPUT_DIR_PATH, pr_name)
    return len(response_json_review_comments_array)


def main():
    def validate_target_gitlab_project():
        conf = configparser.ConfigParser()
        conf.read(COLLECT_TARGET_PROJECT_CONF_PATH)
        gitlab_host = conf.get('DEFAULT', 'GITLAB_HOST')
        target_project_name = conf.get('DEFAULT', 'PROJECT_NAME')
        response = execute_get_api(build_get_gitlab_projects(gitlab_host), build_request_header())
        projects: List = list(filter(lambda pj: pj['name'] == target_project_name, response))
        if len(projects) == 0:
            raise NonExistTargetError()

    try:
        validate_target_gitlab_project()
    except NonExistTargetError:
        print('[ERROR] Non exist target gitlab project')

    retry_execute_git_api(collect_and_write_merge_requests)
