import csv
import os
import re
import shutil
from abc import ABC, abstractmethod
from typing import List, Callable
from jinja2 import Environment, FileSystemLoader
import requests as requests
import configparser

# changeable values
GET_TARGET_PR_STATE_VAL = 'all'  # open, all, close
# GET_TARGET_PR_SORT_VAL = 'created'  # updated, created, popularity, long-running
# GET_TARGET_PR_DIRECTION_VAL = 'desc'  # desc, asc

# constant values
GITHUB_BASEURL = 'https://api.github.com'
GITHUB_GET_PR_API = GITHUB_BASEURL + '/repos/{REPOSITORY_OWNER}/{REPOSITORY}/pulls'
CONF_DIR_PATH = './conf/'
GITHUB_TOKEN_FILE_PATH = CONF_DIR_PATH + 'token'
COLLECT_TARGET_REPOSITORY_CONF_PATH = CONF_DIR_PATH + 'target_repository.conf'
PR_AUTHOR_FILTER_LIST_PATH = CONF_DIR_PATH + 'pr_author_filter_list.txt'
PR_REVIEWER_FILTER_LIST_PATH = CONF_DIR_PATH + 'pr_reviewer_filter_list.txt'
OUTPUT_DIR_PATH = './out/'
PULL_REQUEST_LIST_FILE_NAME = 'pr_list'
TEMPLATES_DIR_PATH = './templates/'
PR_REVIEW_COMMENT_TEMPLATE_FILE_NAME = 'pr_review_comment.j2'


class ICsvWritableDataConverter(ABC):
    @abstractmethod
    def convert_array(self) -> List:
        pass


class ICsvWriter(ABC):
    @abstractmethod
    def write_csv(self, file_name):
        pass


class ICsvConvertAndWriter(ICsvWritableDataConverter, ICsvWriter):
    @abstractmethod
    def convert_array(self) -> List:
        pass

    @abstractmethod
    def write_csv(self, file_name):
        pass


class IMarkdownWritableDataConverter(ABC):
    @abstractmethod
    def convert_json(self):
        pass


class IMarkdownWriter(ABC):
    @abstractmethod
    def write_md(self, sub_dir_name):
        pass


class IMarkdownConvertAndWriter(IMarkdownWritableDataConverter, IMarkdownWriter):
    @abstractmethod
    def convert_json(self):
        pass

    @abstractmethod
    def write_md(self, sub_dir_name):
        pass


def convert_filesystem_path_name(file_path: str):
    replace_file_path = file_path.translate(str.maketrans({'/': '_', ':': '_', ' ': '_'}))
    return re.sub(r'[\\/:*?"<>|]+', '', replace_file_path)  # replace string that can't use to windows file path


def write_csv(file_name: str, data: ICsvConvertAndWriter):
    csv_file_name = convert_filesystem_path_name(file_name) + '.csv'
    try:
        with open(OUTPUT_DIR_PATH + csv_file_name, mode='a', newline='', encoding='CP932', errors='ignore') as f:
            writer = csv.writer(f)
            writer.writerows(data.convert_array())
    except Exception as e:
        print('  -> write file failure:', e)
        return
    print('  -> write file success:', csv_file_name)


def write_md(sub_dir_name: str, file_name: str, data: IMarkdownConvertAndWriter):
    md_file_name = convert_filesystem_path_name(file_name) + '.md'
    try:
        env = Environment(loader=FileSystemLoader(searchpath=TEMPLATES_DIR_PATH, encoding='utf-8'))
        template = env.get_template(PR_REVIEW_COMMENT_TEMPLATE_FILE_NAME)
        md_file_data = template.render(data.convert_json())
        with open(OUTPUT_DIR_PATH + f'{sub_dir_name}/{md_file_name}', mode='w', encoding='CP932', errors='ignore') as f:
            f.write(md_file_data)
    except Exception as e:
        print('  -> write file failure:', e)
        return
    print('  -> write file success:', md_file_name)


def read_text_file(file_path: str):
    try:
        with open(file_path, mode='r') as f:
            lines = f.readlines()
            return list(filter(lambda line: not line.startswith('#'), lines))
    except Exception as e:
        print(f'read {file_path} failure:', e)
        return []


class PullRequestDataList(ICsvConvertAndWriter):
    class PullRequestData(ICsvWritableDataConverter):
        def __init__(self, json_data):
            self.__pr_num: str = str(json_data['number'])
            self.__title: str = json_data['title']
            self.__description: str = json_data['body']
            self.__create_user: str = json_data['user']['login']
            self.__html_url: str = json_data['html_url']
            self.__review_comments_api_url: str = json_data['review_comments_url']
            self.__comments_api_url: str = json_data['comments_url']

        @staticmethod
        def convert_header():
            return ['PR num', 'PR title', 'PR create user', 'PR url' 'review comments api url', 'comments api url']

        def convert_array(self):
            return [self.__pr_num, self.__title, self.__create_user, self.__html_url, self.__review_comments_api_url,
                    self.__comments_api_url]

        @property
        def review_comments_api_url(self) -> str:
            return self.__review_comments_api_url

        @property
        def create_user(self):
            return self.__create_user

        def build_pr_name(self):
            return f'{self.__pr_num}-{self.__title}'

    def __init__(self, response_json_array: List):
        self.__values: List[PullRequestDataList.PullRequestData] = self.__convert(response_json_array)

    @property
    def values(self) -> List[PullRequestData]:
        return self.__values

    @staticmethod
    def __convert(response_json_array: List) -> List[PullRequestData]:
        prs: List[PullRequestDataList.PullRequestData] \
            = [PullRequestDataList.PullRequestData(json_data) for json_data in response_json_array]
        filter_pr_create_user_list = read_text_file(PR_AUTHOR_FILTER_LIST_PATH)
        if len(filter_pr_create_user_list) > 0:
            prs = list(filter(lambda pr: pr.create_user in filter_pr_create_user_list, prs))
        return prs

    def convert_array(self) -> List[List]:
        headers: List[List] = [PullRequestDataList.PullRequestData.convert_header()]
        bodies: List[List] = list(map(lambda pr_data: pr_data.convert_array(), self.values))
        return headers + bodies

    def write_csv(self, file_name):
        if self.is_empty():
            print('  -> response empty. no write file.')
            return
        write_csv(file_name, self)

    def is_empty(self) -> bool:
        return len(self.values) == 0


class PullRequestReviewCommentList(ICsvConvertAndWriter, IMarkdownWriter):
    class PullRequestReviewComment(ICsvWritableDataConverter, IMarkdownConvertAndWriter):
        def __init__(self, json_data, pr_data: PullRequestDataList.PullRequestData):
            self.__id = str(json_data['id'])
            self.__reviewer = json_data['user']['login']
            self.__comment = json_data['body']
            self.__review_comment_url = json_data['_links']['html']['href']
            self.__file_path = json_data['path']
            self.__diff_hunk = json_data['diff_hunk']
            self.__pr_name = pr_data.build_pr_name()
            self.__pr_create_user = pr_data.create_user

        @staticmethod
        def convert_header():
            return ['review id', 'reviewer', 'file name', 'comment', 'review comment url']

        def convert_array(self):
            return [self.__id, self.__reviewer, self.__file_path, self.__comment, self.__review_comment_url]

        def convert_json(self):
            return {
                'title': self.__pr_name,
                'create_user': self.__pr_create_user,
                'reviewer': self.__reviewer,
                'file_path': self.__file_path,
                'diff_hunk': self.__diff_hunk,
                'comment': self.__comment,
                'review_comment_url': self.__review_comment_url
            }

        def write_md(self, dir_name):
            write_md(dir_name, self.__id, self)

        @property
        def reviewer(self):
            return self.__reviewer

    def __init__(self, response_json_array: List, pr_data: PullRequestDataList.PullRequestData):
        self.__values: List[PullRequestReviewCommentList.PullRequestReviewComment] \
            = self.__convert(response_json_array, pr_data)

    @property
    def values(self) -> List[PullRequestReviewComment]:
        return self.__values

    @staticmethod
    def __convert(response_json_array: List, pr_data: PullRequestDataList.PullRequestData) \
            -> List[PullRequestReviewComment]:
        pr_review_comments: List \
            = [PullRequestReviewCommentList.PullRequestReviewComment(json_data, pr_data) for json_data in
               response_json_array]
        filter_pr_reviewer_list = read_text_file(PR_REVIEWER_FILTER_LIST_PATH)
        if len(filter_pr_reviewer_list) > 0:
            pr_review_comments = list(
                filter(lambda comment: comment.reviewer in filter_pr_reviewer_list, pr_review_comments))
        return pr_review_comments

    def convert_array(self) -> List[List]:
        headers: List[List] = [PullRequestReviewCommentList.PullRequestReviewComment.convert_header()]
        bodies: List[List] = list(map(lambda rev_data: rev_data.convert_array(), self.values))
        return headers + bodies

    def write_csv(self, file_name):
        if self.is_empty():
            print('  -> response empty. no write csv file.')
            return
        write_csv(file_name, self)

    def write_md(self, pr_name: str):
        if self.is_empty():
            print('  -> response empty. no write md file.')
            return
        dir_name = convert_filesystem_path_name(pr_name)
        os.makedirs(OUTPUT_DIR_PATH + dir_name + '/', exist_ok=True)
        for value in self.__values:
            value.write_md(dir_name)

    def is_empty(self) -> bool:
        return len(self.values) == 0


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

    def execute_github_api(url: str) -> List:
        headers = build_request_header()
        response = requests.get(url, headers=headers)
        print(response.status_code, response.reason, url)
        if response.status_code == 200:
            return response.json()
        return []

    # Callback-only function used by retry_execute_github_api()
    def collect_and_write_pull_requests(page_count: int, non_arg) -> int:
        api_url = build_collect_pull_requests_api_url(page_count)
        response_json_pr_array = execute_github_api(api_url)
        pr_data_list = PullRequestDataList(response_json_pr_array)
        pr_data_list.write_csv(PULL_REQUEST_LIST_FILE_NAME)
        # get review comment in PR
        for pr_data in pr_data_list.values:
            retry_execute_github_api(collect_and_write_pr_review_comments, pr_data)
        return len(response_json_pr_array)

    # Callback-only function used by retry_execute_github_api()
    def collect_and_write_pr_review_comments(page_count: int, pr_data) -> int:
        api_url = build_collect_pr_review_comments_api_url(pr_data.review_comments_api_url, page_count)
        response_json_review_comments_array = execute_github_api(api_url)
        pr_review_comment_list = PullRequestReviewCommentList(response_json_review_comments_array, pr_data)
        pr_name = pr_data.build_pr_name()
        pr_review_comment_list.write_csv(pr_name)
        pr_review_comment_list.write_md(pr_name)
        return len(response_json_review_comments_array)

    def retry_execute_github_api(api_execute_func: Callable[[int, any], int], *args):
        is_retry = True
        page_count = 1
        while is_retry:
            count = api_execute_func(page_count, args[0] if len(args) != 0 else None)
            page_count += 1
            is_retry = False if count < 100 else True

    print('START')
    if os.path.exists('out/'):
        shutil.rmtree('out/')
    os.makedirs('out/', exist_ok=True)
    # get PR and PR review comment
    retry_execute_github_api(collect_and_write_pull_requests)
    print('END')


main()
