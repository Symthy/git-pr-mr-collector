import configparser
import os
import shutil
# changeable values
import sys
from typing import List

from api.api_executer import execute_get_api, retry_execute_git_api
from domain.pull_request import PullRequestDataList
from domain.pull_request_review_comment import PullRequestReviewCommentList
from exception.error import OptionValueError
from option.option_resolver import resolve_repository_option_value, resolve_pr_option_value

GET_TARGET_PR_STATE_VAL = 'all'  # open, all, close
# GET_TARGET_PR_SORT_VAL = 'created'  # updated, created, popularity, long-running
# GET_TARGET_PR_DIRECTION_VAL = 'desc'  # desc, asc

# constant values
GITHUB_BASEURL = 'https://api.github.com'
GITHUB_GET_PR_API = GITHUB_BASEURL + '/repos/{REPOSITORY_OWNER}/{REPOSITORY}/pulls'
CONF_DIR_PATH = '../conf/'
GITHUB_TOKEN_FILE_PATH = CONF_DIR_PATH + 'github_access_token.txt'
COLLECT_TARGET_REPOSITORY_CONF_PATH = CONF_DIR_PATH + 'target_github_repository.conf'
OUTPUT_DIR_PATH = '../out/github/'
PULL_REQUEST_LIST_FILE_NAME = 'pr_list'
# options
OPTION_SPECIFICATION_COLLECT_PR = '--pr'
OPTION_TARGET_COLLECT_REPOSITORY = '--repo'
OPTIONS = [OPTION_SPECIFICATION_COLLECT_PR, OPTION_TARGET_COLLECT_REPOSITORY]


def build_request_header():
    with open(GITHUB_TOKEN_FILE_PATH) as f:
        github_token = f.read().replace('\n', '')
    return {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': 'token {}'.format(github_token)
    }


def build_get_pull_request_api_base_url(repository_name: str = "") -> str:
    conf = configparser.ConfigParser()
    conf.read(COLLECT_TARGET_REPOSITORY_CONF_PATH)
    repository_owner = conf.get('DEFAULT', 'REPOSITORY_OWNER')
    repository = conf.get('DEFAULT', 'REPOSITORY') if repository_name == "" else repository_name
    pr_api_url = GITHUB_GET_PR_API.replace('{REPOSITORY_OWNER}', repository_owner).replace('{REPOSITORY}', repository)
    return pr_api_url


def build_get_single_pull_request_api_url(pr_num: int, repository: str) -> str:
    return f'{build_get_pull_request_api_base_url(repository)}/{pr_num}'


def build_collect_pull_requests_api_url(page_count: int):
    return f'{build_get_pull_request_api_base_url()}?state={GET_TARGET_PR_STATE_VAL}&page={page_count}&per_page=100'


def build_collect_pr_review_comments_api_url(base_pr_api_url: str, page_count: int):
    return base_pr_api_url + f'?page={page_count}&per_page=100'


def collect_and_write_specified_pull_requests(pr_nums: List[int], repository: str = ""):
    response_json_pr_array = []
    for pr_num in pr_nums:
        api_url = build_get_single_pull_request_api_url(pr_num, repository)
        response_array = execute_get_api(api_url, build_request_header())
        if len(response_array) == 0:
            continue
        response_json_pr_array += response_array
    pr_data_list = PullRequestDataList.create_from_github_pr(response_json_pr_array)
    pr_data_list.write_csv(OUTPUT_DIR_PATH, PULL_REQUEST_LIST_FILE_NAME)
    for pr_data in pr_data_list.values:
        retry_execute_git_api(collect_and_write_pr_review_comments, pr_data)
    return


# Callback-only function used by retry_execute_github_api()
def collect_and_write_all_pull_requests(page_count: int, non_arg) -> int:
    api_url = build_collect_pull_requests_api_url(page_count)
    response_json_pr_array = execute_get_api(api_url, build_request_header())
    pr_data_list = PullRequestDataList.create_from_github_pr(response_json_pr_array)
    pr_data_list.write_csv(OUTPUT_DIR_PATH, PULL_REQUEST_LIST_FILE_NAME)
    # collect review comments in PR
    for pr_data in pr_data_list.values:
        retry_execute_git_api(collect_and_write_pr_review_comments, pr_data)
    return len(response_json_pr_array)


# Callback-only function used by retry_execute_github_api()
def collect_and_write_pr_review_comments(page_count: int, pr_data: PullRequestDataList.PullRequestData) -> int:
    api_url = build_collect_pr_review_comments_api_url(pr_data.review_comments_api_url, page_count)
    response_json_review_comments_array = execute_get_api(api_url, build_request_header())
    pr_review_comment_list = PullRequestReviewCommentList.github_pr(response_json_review_comments_array, pr_data)
    pr_name = pr_data.build_pr_name()
    pr_review_comment_list.write_csv(OUTPUT_DIR_PATH, pr_name)
    pr_review_comment_list.write_md(OUTPUT_DIR_PATH, pr_name)
    return len(response_json_review_comments_array)


def main(args: List[str]):
    if os.path.exists(OUTPUT_DIR_PATH):
        shutil.rmtree(OUTPUT_DIR_PATH)
    os.makedirs(OUTPUT_DIR_PATH, exist_ok=True)

    if OPTION_SPECIFICATION_COLLECT_PR in args:
        print('=== START - collect specified pull requests ===')
        target_repository = resolve_repository_option_value(OPTION_TARGET_COLLECT_REPOSITORY,
                                                            OPTION_SPECIFICATION_COLLECT_PR, args)
        target_pr_list = []
        try:
            target_pr_list = resolve_pr_option_value(OPTION_SPECIFICATION_COLLECT_PR, OPTIONS, args)
        except OptionValueError:
            print('[ERROR] Invalid pr option value. option format is \"--pr <PR num>[ <PR num>]...\"')
        if not len(target_pr_list) == 0:
            pr_list_str = ', '.join(map(str, target_pr_list))
            print(f'[Info] collect target PR list: {pr_list_str}')
            collect_and_write_specified_pull_requests(target_pr_list, target_repository)
        print('=== END - collect specified pull requests ===')
    else:
        print('=== START - collect pull requests ===')
        # get PR and PR review comment
        retry_execute_git_api(collect_and_write_all_pull_requests)
        print('=== END - collect pull requests ===')


main(sys.argv)
