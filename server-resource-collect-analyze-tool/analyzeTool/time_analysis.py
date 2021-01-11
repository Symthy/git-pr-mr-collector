import glob
import sys
from typing import List
import datetime as dt
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt

from analyzeTool.analysis_util import convert_date_time, create_max_value_row, create_average_value_row, write_csv_file

START_PREFIXES = ['start::']
END_PREFIXES = ['end::']
DATE_TIME_FORMAT = '%d/%m/%y %H:%M:%S.%f'
GRAPH_TITLE = 'TOTAL TIME per CASE [sec]'
OUTPUT_FILE_NAME = 'total_time_result'
HEADER_PREFIX = 'case'


def view_line_graph(title: str, header: List[str], array2d: List[List[str]]):
    """
    Description:
        create and view line graph by matplotlib.
    :param title: graph title.
    :param header: top line of output file. top line is '' and process id.
    :param array2d: 2d array (row: date time, column: process). row 0 is date time.
    :return: void
    """
    times = [convert_date_time(array2d[i][0]) for i in range(len(array2d)) if i < len(array2d)]
    fig, axes = plt.subplots()
    fig.subplots_adjust(bottom=0.2, top=0.95)
    for col in range(len(array2d[0])):
        y_values = []
        for row in range(len(array2d)):
            y_values.append(array2d[row][col] if array2d[row][col] != '' else None)
        axes.plot(times, y_values, label=header[col])
    axes.xaxis.set_major_locator(ticker.AutoLocator())
    axes.set_title(title)
    axes.set_xlabel('Count')
    axes.set_ylabel('Total Time [sec]')
    axes.set_ylim(bottom=0)
    axes.legend()
    axes.grid()
    plt.xticks(rotation=30)


def calculate_time(start_time: dt, end_time: dt):
    if not start_time or not end_time:
        return 0
    td = end_time - start_time
    return td.total_seconds()


def analyze_time_log_lines(lines: List[str], array_2d: List[List]):
    start_time: dt = None
    start_prefix_index: int = -1
    end_time: dt = None
    record: List[int] = []
    row_num: int = 1
    for line in lines:
        for index, prefix in enumerate(START_PREFIXES):
            if line.startswith(prefix):
                length: int = len(prefix)
                start_time: dt = convert_date_time(line[length:], DATE_TIME_FORMAT)
                start_prefix_index = index
        for index, prefix in enumerate(END_PREFIXES):
            if line.startswith(prefix) and index == start_prefix_index:
                length: int = len(prefix)
                end_time: dt = convert_date_time(line[length:], DATE_TIME_FORMAT)
                record += [calculate_time(start_time, end_time)]
        if len(record) >= len(START_PREFIXES):
            array_2d.append([row_num] + record)
            row_num += 1
            start_time = None
            start_prefix_index = -1
            end_time = None


def analyze_time_logs(lines: List[str]):
    array2d: List[List] = []
    analyze_time_log_lines(lines, array2d)
    header: List[str] = ['count'] + [HEADER_PREFIX + str(i) for i in range(len(array2d[0])) if i != 0]
    view_line_graph(GRAPH_TITLE, header, array2d)
    array2d.append(['MAX:'] + create_max_value_row(array2d))
    array2d.append(['AVG:'] + create_average_value_row(array2d))
    write_csv_file(OUTPUT_FILE_NAME, header, array2d)
    plt.show()


def main(args: List[str]):
    """

    :param args: command line arguments
    :return: void
    """
    is_view_graph = True
    file_paths: List[str] = glob.glob("../input/test*.log")
    lines = []
    for file_path in file_paths:
        with open(file_path, 'r', encoding="utf-8_sig") as f:
            lines += f.readlines()
    analyze_time_logs(lines)


main(sys.argv)
