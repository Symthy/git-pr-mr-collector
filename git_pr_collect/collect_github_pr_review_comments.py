import configparser
import os
import shutil

# changeable values
from utils.api_executer import execute_get_api, retry_execute_git_api
from utils.pr_domain import PullRequestDataList, PullRequestReviewCommentList

GET_TARGET_PR_STATE_VAL = 'all'  # open, all, close
# GET_TARGET_PR_SORT_VAL = 'created'  # updated, created, popularity, long-running
# GET_TARGET_PR_DIRECTION_VAL = 'desc'  # desc, asc

# constant values
GITHUB_BASEURL = 'https://api.github.com'
GITHUB_GET_PR_API = GITHUB_BASEURL + '/repos/{REPOSITORY_OWNER}/{REPOSITORY}/pulls'
CONF_DIR_PATH = './conf/'
GITHUB_TOKEN_FILE_PATH = CONF_DIR_PATH + 'token'
COLLECT_TARGET_REPOSITORY_CONF_PATH = CONF_DIR_PATH + 'target_repository.conf'
OUTPUT_DIR_PATH = './out/github/'
PULL_REQUEST_LIST_FILE_NAME = 'pr_list'


def main():
    def build_request_header():
        with open(GITHUB_TOKEN_FILE_PATH) as f:
            github_token = f.read()
        return {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': 'token {}'.format(github_token)
        }

    def build_collect_pull_requests_api_url(page_count: int):
        conf = configparser.ConfigParser()
        conf.read(COLLECT_TARGET_REPOSITORY_CONF_PATH)
        repository_owner = conf.get('DEFAULT', 'REPOSITORY_OWNER')
        repository_name = conf.get('DEFAULT', 'REPOSITORY')
        pr_api_url = GITHUB_GET_PR_API.replace('{REPOSITORY_OWNER}', repository_owner).replace('{REPOSITORY}',
                                                                                               repository_name)
        return pr_api_url + '?state=' + GET_TARGET_PR_STATE_VAL + f'&page={page_count}&per_page=100'

    def build_collect_pr_review_comments_api_url(base_url: str, page_count: int):
        return base_url + f'?page={page_count}&per_page=100'

    # Callback-only function used by retry_execute_github_api()
    def collect_and_write_pull_requests(page_count: int, non_arg) -> int:
        api_url = build_collect_pull_requests_api_url(page_count)
        response_json_pr_array = execute_get_api(api_url, build_request_header())
        pr_data_list = PullRequestDataList.github_pr(response_json_pr_array)
        pr_data_list.write_csv(OUTPUT_DIR_PATH, PULL_REQUEST_LIST_FILE_NAME)
        # get review comment in PR
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

    print('START')
    if os.path.exists(OUTPUT_DIR_PATH):
        shutil.rmtree(OUTPUT_DIR_PATH)
    os.makedirs(OUTPUT_DIR_PATH, exist_ok=True)
    # get PR and PR review comment
    retry_execute_git_api(collect_and_write_pull_requests)
    print('END')


main()
