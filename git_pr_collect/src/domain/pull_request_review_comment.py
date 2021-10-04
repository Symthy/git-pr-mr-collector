import os
from typing import List

from domain.pull_request import PullRequestDataList
from file.file_accessor import ICsvConvertAndWriter, IMarkdownWriter, ICsvDataConverter, \
    IMarkdownConvertAndWriter, read_filter_list_text_file, convert_windows_filesystem_path, write_csv_file, \
    write_md_file

PR_REVIEWER_FILTER_LIST_PATH = '../conf/pr_reviewer_filter_list.txt'
MR_REVIEWER_FILTER_LIST_PATH = '../conf/mr_reviewer_filter_list.txt'


class PullRequestReviewCommentList(ICsvConvertAndWriter, IMarkdownWriter):
    class PullRequestReviewComment(ICsvDataConverter, IMarkdownConvertAndWriter):
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
        def create_from_github_pr(json_data, pr_data: PullRequestDataList.PullRequestData) -> __init__:
            return PullRequestReviewCommentList.PullRequestReviewComment(str(json_data['id']),
                                                                         json_data['user']['login'], json_data['body'],
                                                                         json_data['path'], json_data['diff_hunk'],
                                                                         json_data['_links']['html']['href'],
                                                                         pr_data.build_pr_name(), pr_data.create_user)

        @staticmethod
        def create_from_gitlab_mr(json_data, pr_data: PullRequestDataList.PullRequestData) -> __init__:
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
            write_md_file(output_dir_path, dir_name, self.__review_id, self)

        @property
        def reviewer(self):
            return self.__reviewer

    def __init__(self, values):
        self.__values: List[PullRequestReviewCommentList.PullRequestReviewComment] = values

    @staticmethod
    def github_pr(response_json_array: List, pr_data: PullRequestDataList.PullRequestData) -> __init__:
        pr_review_comments: List \
            = [PullRequestReviewCommentList.PullRequestReviewComment.create_from_github_pr(json_data, pr_data) for
               json_data in
               response_json_array]
        filter_pr_reviewer_list = read_filter_list_text_file(PR_REVIEWER_FILTER_LIST_PATH)
        if len(filter_pr_reviewer_list) > 0:
            pr_review_comments = list(
                filter(lambda comment: comment.reviewer in filter_pr_reviewer_list, pr_review_comments))
        return PullRequestReviewCommentList(pr_review_comments)

    @staticmethod
    def gitlab_mr(response_json_array: List, pr_data: PullRequestDataList.PullRequestData) -> __init__:
        pr_review_comments: List \
            = [PullRequestReviewCommentList.PullRequestReviewComment.create_from_gitlab_mr(json_data, pr_data) for
               json_data in
               response_json_array]
        filter_mr_reviewer_list = read_filter_list_text_file(MR_REVIEWER_FILTER_LIST_PATH)
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
        write_csv_file(output_dir_path, file_name, self)

    def write_md(self, output_dir_path: str, pr_name: str):
        if self.is_empty():
            print('  -> response empty. no write md file.')
            return
        dir_name = convert_windows_filesystem_path(pr_name)
        os.makedirs(output_dir_path + dir_name + '/', exist_ok=True)
        for value in self.__values:
            value.write_md(output_dir_path, dir_name)

    def is_empty(self) -> bool:
        return len(self.values) == 0
