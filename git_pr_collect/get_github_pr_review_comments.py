import csv
import os
import shutil
from abc import ABC, abstractmethod
from typing import List

import requests as requests

OWNER_NAME = "Symthy"
REPOSITORY = "TodoList-ts-pre"

GITHUB_BASEURL = "https://api.github.com"
GITHUB_GET_PULL_API = GITHUB_BASEURL + "/repos/" + OWNER_NAME + "/" + REPOSITORY + "/pulls"
STATE_VAL = "all"  # open, all, close
SORT_VAL = "created"  # updated, created, popularity, long-running
DIRECTION_VAL = "desc"  # desc, asc

FILTER_PR_CREATOR = [

]
FILTER_REVIEW_COMMENTER = [

]


class ICsvWritableDataConverter(ABC):
    @abstractmethod
    def convert_header(self) -> List:
        pass

    @abstractmethod
    def convert_body(self) -> List:
        pass


def write_csv(file_title: str, data: ICsvWritableDataConverter):
    file_name = file_title.translate(str.maketrans({'/': '_', ':': '_', ' ': '_'}))
    with open('out/' + file_name + '.csv', mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data.convert_header())
        writer.writerows(data.convert_body())


class PullRequestDataList(ICsvWritableDataConverter):
    class PullRequestData:
        def __init__(self, json_data):
            self.pr_num: int = json_data['number']
            self.title: str = json_data['title']
            self.create_user: str = json_data['user']['login']
            self.review_comments_url: str = json_data['review_comments_url']
            self.comments_url: str = json_data['comments_url']

        @staticmethod
        def convert_header():
            return ['PR num', 'PR title', 'PR create user', 'review comments url', 'comments url']

        def convert_array(self):
            return [self.pr_num, self.title, self.create_user, self.review_comments_url, self.comments_url]

    def __init__(self, json_array: List):
        self.values = self.__convert(json_array)

    @staticmethod
    def __convert(json_array: List) -> List[PullRequestData]:
        prs: List[PullRequestDataList.PullRequestData] \
            = [PullRequestDataList.PullRequestData(json_data) for json_data in json_array]
        if len(FILTER_PR_CREATOR) > 0:
            prs = list(filter(lambda pr: pr.create_user in FILTER_PR_CREATOR, prs))
        return prs

    def convert_header(self) -> List:
        return PullRequestDataList.PullRequestData.convert_header()

    def convert_body(self) -> List[List]:
        arrays: List[List] = list(map(lambda pr_data: pr_data.convert_array(), self.values))
        return arrays

    def write_csv(self, file_title):
        write_csv(file_title, self)


class PullRequestReviewCommentList(ICsvWritableDataConverter):
    class PullRequestReviewComment:
        def __init__(self, json_data):
            self.id = json_data['pull_request_review_id']
            self.reviewer = json_data['user']['login']
            self.comment = json_data['body']
            self.review_comment_url = json_data['url']
            self.file_path = json_data['path']
            self.diff_hunk = json_data['diff_hunk']

        @staticmethod
        def convert_header():
            return ['review id', 'reviewer', 'comment', 'file name', 'review comment url', 'diff']

        def convert_array(self):
            return [self.id, self.reviewer, self.comment, self.file_path, self.review_comment_url, self.diff_hunk]

    def __init__(self, json_array: List):
        self.values = self.__convert(json_array)

    @staticmethod
    def __convert(json_array: List) -> List[PullRequestReviewComment]:
        review_comments: List \
            = [PullRequestReviewCommentList.PullRequestReviewComment(json_data) for json_data in json_array]
        if len(FILTER_REVIEW_COMMENTER) > 0:
            review_comments = list(filter(lambda pr: pr.create_user in FILTER_PR_CREATOR, review_comments))
        return review_comments

    def convert_header(self) -> List:
        return PullRequestReviewCommentList.PullRequestReviewComment.convert_header()

    def convert_body(self) -> List[List]:
        arrays: List[List] = list(map(lambda rev_data: rev_data.convert_array(), self.values))
        return arrays

    def write_csv(self, file_title):
        write_csv(file_title, self)


def main():
    def build_header():
        with open('./conf/token') as f:
            github_token = f.read()
        return {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': 'token {}'.format(github_token)
        }

    def build_get_pulls_api_url(page_count):
        return GITHUB_GET_PULL_API + '?state=' + STATE_VAL + f'&page={page_count}&per_page=100'

    def execute_github_api(url):
        headers = build_header()
        response = requests.get(url, headers=headers)
        return response.json()

    if os.path.exists('out/'):
        shutil.rmtree('out/')
    os.makedirs('out/', exist_ok=True)

    # get PR
    is_get_pr_retry = True
    pr_page_count = 1
    while is_get_pr_retry:
        api_url = build_get_pulls_api_url(pr_page_count)
        pr_json_array = execute_github_api(api_url)
        pr_data_list = PullRequestDataList(pr_json_array)
        pr_data_list.write_csv('pr_list')

        # get PR review comment
        for pr_data in pr_data_list.values:
            is_get_review_comment_retry = True
            review_comment_page_count = 1
            while is_get_review_comment_retry:
                comments_json_array = execute_github_api(
                    pr_data.review_comments_url + f'?page={review_comment_page_count}&per_page=100')
                pr_review_comment_list = PullRequestReviewCommentList(comments_json_array)
                pr_review_comment_list.write_csv(f'{pr_data.pr_num}-{pr_data.title}')

                review_comment_page_count += 1
                is_get_review_comment_retry = False if len(comments_json_array) < 100 else True

        pr_page_count += 1
        is_get_pr_retry = False if len(pr_json_array) < 100 else True


main()
