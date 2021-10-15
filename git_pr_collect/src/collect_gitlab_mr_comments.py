import configparser
import os
import shutil
from typing import List

from api.api_executer import execute_get_api, retry_execute_git_api
from domain.pull_request import PullRequestDataList
from domain.pull_request_review_comment import PullRequestReviewCommentList
from exception.error import NonExistTargetError

# constant values
GITLAB_BASEURL = 'http://{GITLAB_HOST}/api/v4'
GITLAB_GET_PROJECTS_URL = GITLAB_BASEURL + '/projects'
GITLAB_GET_MR_URL = GITLAB_GET_PROJECTS_URL + '/{PROJECT_ID}/merge_requests'
CONF_DIR_PATH = '../conf/'
GITLAB_TOKEN_FILE_PATH = CONF_DIR_PATH + 'gitlab_access_token.txt'
COLLECT_TARGET_PROJECT_CONF_PATH = CONF_DIR_PATH + 'target_gitlab_project.conf'
MERGE_REQUEST_LIST_FILE_NAME = 'mr_list'
OUTPUT_DIR_PATH = '../out/gitlab/'


def build_request_header():
    with open(GITLAB_TOKEN_FILE_PATH) as f:
        gitlab_access_token = f.read().replace('\n', '')
    return {
        'Authorization': 'Bearer ' + gitlab_access_token
    }


def build_get_merge_request_api_base_url(project_name: str = "") -> str:
    conf = configparser.ConfigParser()
    conf.read(COLLECT_TARGET_PROJECT_CONF_PATH)
    gitlab_host = conf.get('DEFAULT', 'GITLAB_HOST')
    target_project_id = conf.get('DEFAULT', 'PROJECT_ID') if project_name == "" else project_name
    mr_api_url = GITLAB_GET_MR_URL.replace('{GITLAB_HOST}', gitlab_host).replace('{PROJECT_ID}', target_project_id)
    return mr_api_url


def build_get_gitlab_projects(gitlab_host: str) -> str:
    return GITLAB_GET_PROJECTS_URL.replace('{GITLAB_HOST}', gitlab_host)


def build_collect_gitlab_merge_requests_api_url(page_count: int) -> str:
    return f'{build_get_merge_request_api_base_url()}?per_page=100&page={str(page_count)}'


def build_collect_gitlab_mr_comments_api_url(page_count: int, merge_request_iid: str):
    return f'{build_get_merge_request_api_base_url()}/{merge_request_iid}/discussions?per_page=100&page={str(page_count)}'


def build_get_single_merge_request_api_url(pr_num: int, repository: str) -> str:
    pr_api_url = build_get_merge_request_api_base_url(repository)
    return f'{pr_api_url}/{pr_num}'


def collect_and_write_specified_merge_requests(pr_nums: List[int], repository: str = ""):
    response_json_pr_array = []
    for pr_num in pr_nums:
        api_url = build_get_single_merge_request_api_url(pr_num, repository)
        response_array = execute_get_api(api_url, build_request_header())
        if len(response_array) == 0:
            continue
        response_json_pr_array += response_array
    pr_data_list = PullRequestDataList.create_from_github_pr(response_json_pr_array)
    pr_data_list.write_csv(OUTPUT_DIR_PATH, MERGE_REQUEST_LIST_FILE_NAME)
    for pr_data in pr_data_list.values:
        retry_execute_git_api(collect_and_write_mr_comments, pr_data)
    return


# Callback-only function used by retry_execute_git_api()
def collect_and_write_merge_requests(page_count: int, non_arg) -> int:
    api_url = build_collect_gitlab_merge_requests_api_url(page_count)
    response_json_pr_array = execute_get_api(api_url, build_request_header())
    pr_data_list = PullRequestDataList.create_from_gitlab_mr(response_json_pr_array)
    pr_data_list.write_csv(OUTPUT_DIR_PATH, MERGE_REQUEST_LIST_FILE_NAME)
    # get discussions in MR
    for pr_data in pr_data_list.values:
        retry_execute_git_api(collect_and_write_mr_comments, pr_data)
    return len(response_json_pr_array)


# Callback-only function used by retry_execute_git_api()
def collect_and_write_mr_comments(page_count: int, pr_data: PullRequestDataList.PullRequestData) -> int:
    api_url = build_collect_gitlab_mr_comments_api_url(page_count, pr_data.pr_num)
    response_json_discussion_array = execute_get_api(api_url, build_request_header())
    pr_review_comment_list = PullRequestReviewCommentList.create_from_gitlab_mr(response_json_discussion_array, pr_data)
    pr_name = pr_data.build_pr_name()
    pr_review_comment_list.write_csv(OUTPUT_DIR_PATH, pr_name)
    # TODO: if can get diff of comment part, output md file
    # pr_review_comment_list.write_md(OUTPUT_DIR_PATH, pr_name)
    return len(response_json_discussion_array)


def main():
    def validate_target_gitlab_project():
        conf = configparser.ConfigParser()
        conf.read(COLLECT_TARGET_PROJECT_CONF_PATH)
        gitlab_host = conf.get('DEFAULT', 'GITLAB_HOST')
        target_project_id = conf.get('DEFAULT', 'PROJECT_ID')
        response = execute_get_api(build_get_gitlab_projects(gitlab_host), build_request_header())
        projects: List = list(filter(lambda pj: pj['id'] == target_project_id, response))
        if len(projects) == 0:
            raise NonExistTargetError()

    # try:
    #     validate_target_gitlab_project()
    # except NonExistTargetError:
    #     print('[ERROR] Non exist target gitlab project')
    if os.path.exists(OUTPUT_DIR_PATH):
        shutil.rmtree(OUTPUT_DIR_PATH)
    os.makedirs(OUTPUT_DIR_PATH, exist_ok=True)
    retry_execute_git_api(collect_and_write_merge_requests)


main()
