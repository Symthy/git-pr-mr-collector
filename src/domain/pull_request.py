from typing import List, Optional

from file.file_accessor import ICsvConvertAndWriter, ICsvDataConverter, read_filter_list_text_file, write_csv_file

PR_AUTHOR_FILTER_LIST_PATH = '../conf/pr_author_filter_list.txt'
MR_AUTHOR_FILTER_LIST_PATH = '../conf/mr_author_filter_list.txt'


class PullRequestDataList(ICsvConvertAndWriter):
    class PullRequestData(ICsvDataConverter):
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
    def create_from_github_pr(response_json_array, is_filter: bool = True) -> __init__:
        prs: List[PullRequestDataList.PullRequestData] \
            = [PullRequestDataList.PullRequestData.create_from_github_pr(json_data) for json_data in
               response_json_array]
        if is_filter:
            filter_pr_create_user_list = read_filter_list_text_file(PR_AUTHOR_FILTER_LIST_PATH)
            if len(filter_pr_create_user_list) > 0:
                prs = list(filter(lambda pr: pr.create_user in filter_pr_create_user_list, prs))
        return PullRequestDataList(prs)

    @staticmethod
    def create_from_gitlab_mr(response_json_array, is_filter: bool = True) -> __init__:
        prs: List[PullRequestDataList.PullRequestData] \
            = [PullRequestDataList.PullRequestData.create_from_gitlab_mr(json_data) for json_data in
               response_json_array]
        if is_filter:
            filter_mr_author_list = read_filter_list_text_file(MR_AUTHOR_FILTER_LIST_PATH)
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
        write_csv_file(output_dir_path, file_name, self)

    def is_empty(self) -> bool:
        return len(self.values) == 0
