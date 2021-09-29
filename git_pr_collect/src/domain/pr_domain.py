import os
from typing import List, Optional

from file.file_accessor import ICsvConvertAndWriter, ICsvWritableDataConverter, IMarkdownConvertAndWriter, \
    IMarkdownWriter, convert_filesystem_path_name, read_text_file, write_csv, write_md

PR_AUTHOR_FILTER_LIST_PATH = '../conf/pr_author_filter_list.txt'
PR_REVIEWER_FILTER_LIST_PATH = '../conf/pr_reviewer_filter_list.txt'
MR_AUTHOR_FILTER_LIST_PATH = '../conf/mr_author_filter_list.txt'
MR_REVIEWER_FILTER_LIST_PATH = '../conf/mr_reviewer_filter_list.txt'


class PullRequestDataList(ICsvConvertAndWriter):
    class PullRequestData(ICsvWritableDataConverter):
        def __init__(self, pr_num: str, title: str, description: str, create_user: str, html_url: str,
                     review_comments_url: Optional[str], comments_api_url: Optional[str]):
            self.__pr_num: str = pr_num
            self.__title: str = title
            self.__description: str = description
            self.__create_user: str = create_user
            self.__html_url: str = html_url
            # under github only
            self.__review_comments_api_url: str = review_comments_url
            self.__comments_api_url: str = comments_api_url

        @staticmethod
        def create_from_github_pr(json_data) -> __init__:
            return PullRequestDataList.PullRequestData(str(json_data['number']), json_data['title'], json_data['body'],
                                                       json_data['user']['login'], json_data['html_url'],
                                                       json_data['review_comments_url'], json_data['comments_url'])

        @staticmethod
        def create_from_gitlab_mr(json_data) -> __init__:
            return PullRequestDataList.PullRequestData(str(json_data['iid']), json_data['title'],
                                                       json_data['description'], json_data['author']['name'],
                                                       json_data['web_url'], None, None)

        @staticmethod
        def convert_header():
            return ['PR num', 'PR title', 'PR create user', 'PR page link']

        def convert_array(self):
            return [self.__pr_num, self.__title, self.__create_user, self.__html_url]

        @property
        def pr_num(self) -> str:
            return self.__pr_num

        @property
        def review_comments_api_url(self) -> str:
            return self.__review_comments_api_url

        @property
        def create_user(self):
            return self.__create_user

        def build_pr_name(self):
            return f'{self.__pr_num}-{self.__title}'

    def __init__(self, values: List[PullRequestData]):
        self.__values: List[PullRequestDataList.PullRequestData] = values

    @staticmethod
    def create_from_github_pr(response_json_array) -> __init__:
        prs: List[PullRequestDataList.PullRequestData] \
            = [PullRequestDataList.PullRequestData.create_from_github_pr(json_data) for json_data in
               response_json_array]
        filter_pr_create_user_list = read_text_file(PR_AUTHOR_FILTER_LIST_PATH)
        if len(filter_pr_create_user_list) > 0:
            prs = list(filter(lambda pr: pr.create_user in filter_pr_create_user_list, prs))
        return PullRequestDataList(prs)

    @staticmethod
    def create_from_gitlab_mr(response_json_array) -> __init__:
        prs: List[PullRequestDataList.PullRequestData] \
            = [PullRequestDataList.PullRequestData.create_from_gitlab_mr(json_data) for json_data in
               response_json_array]
        filter_mr_author_list = read_text_file(MR_AUTHOR_FILTER_LIST_PATH)
        if len(filter_mr_author_list) > 0:
            prs = list(filter(lambda pr: pr.create_user in filter_mr_author_list, prs))
        return PullRequestDataList(prs)

    @property
    def values(self) -> List[PullRequestData]:
        return self.__values

    def convert_array(self) -> List[List]:
        headers: List[List] = [PullRequestDataList.PullRequestData.convert_header()]
        bodies: List[List] = list(map(lambda pr_data: pr_data.convert_array(), self.values))
        return headers + bodies

    def write_csv(self, output_dir_path, file_name):
        if self.is_empty():
            print('  -> response empty. no write file.')
            return
        write_csv(output_dir_path, file_name, self)

    def is_empty(self) -> bool:
        return len(self.values) == 0


class PullRequestReviewCommentList(ICsvConvertAndWriter, IMarkdownWriter):
    class PullRequestReviewComment(ICsvWritableDataConverter, IMarkdownConvertAndWriter):
        def __init__(self, review_id: str, reviewer: str, comment: str, file_path: str, diff_hunk: str,
                     review_comment_url: str, pr_name: str, pr_create_user: str):
            self.__review_id = review_id
            self.__reviewer = reviewer
            self.__comment = comment
            self.__file_path = file_path
            self.__diff_hunk = diff_hunk
            self.__review_comment_url = review_comment_url
            self.__pr_name = pr_name
            self.__pr_create_user = pr_create_user

        @staticmethod
        def github_pr(json_data, pr_data: PullRequestDataList.PullRequestData) -> __init__:
            return PullRequestReviewCommentList.PullRequestReviewComment(str(json_data['id']),
                                                                         json_data['user']['login'], json_data['body'],
                                                                         json_data['path'], json_data['diff_hunk'],
                                                                         json_data['_links']['html']['href'],
                                                                         pr_data.build_pr_name(), pr_data.create_user)

        @staticmethod
        def gitlab_mr(json_data, pr_data: PullRequestDataList.PullRequestData) -> __init__:
            return PullRequestReviewCommentList.PullRequestReviewComment(str(json_data['id']),
                                                                         json_data['author']['name'], json_data['body'],
                                                                         '[Nothing]', '[Nothing]', '[Nothing]',
                                                                         pr_data.build_pr_name(), pr_data.create_user)

        @staticmethod
        def convert_header():
            return ['review id', 'reviewer', 'file name', 'comment', 'review comment link']

        def convert_array(self):
            return [self.__review_id, self.__reviewer, self.__file_path, self.__comment, self.__review_comment_url]

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

        def write_md(self, output_dir_path, dir_name):
            write_md(output_dir_path, dir_name, self.__review_id, self)

        @property
        def reviewer(self):
            return self.__reviewer

    def __init__(self, values):
        self.__values: List[PullRequestReviewCommentList.PullRequestReviewComment] = values

    @staticmethod
    def github_pr(response_json_array: List, pr_data: PullRequestDataList.PullRequestData) -> __init__:
        pr_review_comments: List \
            = [PullRequestReviewCommentList.PullRequestReviewComment.github_pr(json_data, pr_data) for json_data in
               response_json_array]
        filter_pr_reviewer_list = read_text_file(PR_REVIEWER_FILTER_LIST_PATH)
        if len(filter_pr_reviewer_list) > 0:
            pr_review_comments = list(
                filter(lambda comment: comment.reviewer in filter_pr_reviewer_list, pr_review_comments))
        return PullRequestReviewCommentList(pr_review_comments)

    @staticmethod
    def gitlab_mr(response_json_array: List, pr_data: PullRequestDataList.PullRequestData) -> __init__:
        pr_review_comments: List \
            = [PullRequestReviewCommentList.PullRequestReviewComment.gitlab_mr(json_data, pr_data) for json_data in
               response_json_array]
        filter_mr_reviewer_list = read_text_file(MR_REVIEWER_FILTER_LIST_PATH)
        if len(filter_mr_reviewer_list) > 0:
            pr_review_comments = list(
                filter(lambda comment: comment.reviewer in filter_mr_reviewer_list, pr_review_comments))
        return PullRequestReviewCommentList(pr_review_comments)

    @property
    def values(self) -> List[PullRequestReviewComment]:
        return self.__values

    def convert_array(self) -> List[List]:
        headers: List[List] = [PullRequestReviewCommentList.PullRequestReviewComment.convert_header()]
        bodies: List[List] = list(map(lambda rev_data: rev_data.convert_array(), self.values))
        return headers + bodies

    def write_csv(self, output_dir_path, file_name):
        if self.is_empty():
            print('  -> response empty. no write csv file.')
            return
        write_csv(output_dir_path, file_name, self)

    def write_md(self, output_dir_path: str, pr_name: str):
        if self.is_empty():
            print('  -> response empty. no write md file.')
            return
        dir_name = convert_filesystem_path_name(pr_name)
        os.makedirs(output_dir_path + dir_name + '/', exist_ok=True)
        for value in self.__values:
            value.write_md(output_dir_path, dir_name)

    def is_empty(self) -> bool:
        return len(self.values) == 0
