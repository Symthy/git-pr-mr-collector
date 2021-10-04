import csv
import re
from abc import abstractmethod, ABC
from typing import List

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR_PATH = '../templates/'
PR_REVIEW_COMMENT_TEMPLATE_FILE_NAME = 'pr_review_comment.j2'


class ICsvDataConverter(ABC):
    @abstractmethod
    def convert_array(self) -> List:
        pass


class ICsvWriter(ABC):
    @abstractmethod
    def write_csv(self, output_dir_path, file_name):
        pass


class ICsvConvertAndWriter(ICsvDataConverter, ICsvWriter):
    @abstractmethod
    def convert_array(self) -> List:
        pass

    @abstractmethod
    def write_csv(self, output_dir_path, file_name):
        pass


class IMarkdownDataConverter(ABC):
    @abstractmethod
    def convert_json(self):
        pass


class IMarkdownWriter(ABC):
    @abstractmethod
    def write_md(self, output_dir_path, sub_dir_name):
        pass


class IMarkdownConvertAndWriter(IMarkdownDataConverter, IMarkdownWriter):
    @abstractmethod
    def convert_json(self):
        pass

    @abstractmethod
    def write_md(self, output_dir_path, sub_dir_name):
        pass


def write_csv_file(output_dir_path: str, file_name: str, data: ICsvDataConverter):
    csv_file_name = convert_windows_filesystem_path(file_name) + '.csv'
    try:
        with open(output_dir_path + csv_file_name, mode='a', newline='', encoding='utf-8', errors='ignore') as f:
            writer = csv.writer(f)
            writer.writerows(data.convert_array())
    except Exception as e:
        print('  -> write file failure:', e)
        return
    print('  -> write file success:', csv_file_name)


def write_md_file(output_dir_path: str, sub_dir_name: str, file_name: str, data: IMarkdownDataConverter):
    md_file_name = convert_windows_filesystem_path(file_name) + '.md'
    try:
        env = Environment(loader=FileSystemLoader(searchpath=TEMPLATES_DIR_PATH, encoding='utf-8'))
        template = env.get_template(PR_REVIEW_COMMENT_TEMPLATE_FILE_NAME)
        md_file_data = template.render(data.convert_json())
        with open(output_dir_path + f'{sub_dir_name}/{md_file_name}', mode='w', encoding='utf-8', errors='ignore') as f:
            f.write(md_file_data)
    except Exception as e:
        print('  -> write file failure:', e)
        return
    print('  -> write file success:', md_file_name)


def convert_windows_filesystem_path(file_path: str):
    replace_file_path = file_path.translate(str.maketrans({'/': '_', ':': '_', ' ': '_'}))
    return re.sub(r'[\\/:*?"<>|]+', '', replace_file_path)  # replace string that can't use to windows file path


def read_filter_list_text_file(file_path: str):
    try:
        with open(file_path, mode='r') as f:
            lines = f.readlines()
            return list(filter(lambda line: not line.startswith('#'), lines))
    except Exception as e:
        print(f'read {file_path} failure:', e)
        return []
