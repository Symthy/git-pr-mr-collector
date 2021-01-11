import csv
import glob
import sys
from typing import List, Optional, Dict

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from analyzeTool.analysis_util import convert_date_time, convert_option_date_time, create_max_value_row, \
    create_average_value_row, is_contain_rage_from_start_to_end, write_csv_file

# Constant Value
FILESYSTEM_INDEX = 0
ONE_K_BLOCKS_INDEX = 1
USED_INDEX = 2
AVAILABLE_INDEX = 3
USE_PERCENT_INDEX = 4
MOUNTED_ON_INDEX = 5
LOG_ONE_BLOCK_START_MARK = '###### start '
LOG_ONE_BLOCK_START_LINE_SLICE_SIZE = 7
DATE_TIME_FORMAT = '%Y-%m-%d %H%M%S'

# Variables
FILESYSTEM_FILTER_TOP_STRING = '/dev/s'
GRAPH_TITLE = 'Disk Usage'
OUTPUT_FILE_NAME = 'df_result'
START_DATETIME_OPTION = '--startTime'
END_DATETIME_OPTION = '--endTime'
GRAPH_TIME_RANGE_HOUR_OPTION = '--hour'


def view_line_graph(title: str, total: int, header: List[str], array2d: List[List[str]],
                    is_time_range_hour_option: bool, target_col: int):
    """
    Description:
        create and view line graph by matplotlib.
    :param is_time_range_hour_option:
    :param total: memory total value
    :param title: graph title.
    :param header: top line of output file. top line is '' and process id.
    :param array2d: 2d array (row: date time, column: process). row 0 is date time.
    :return: void
    """
    times = [convert_date_time(array2d[i][0]) for i in range(len(array2d)) if i < len(array2d)]
    fig, axes = plt.subplots()
    fig.subplots_adjust(bottom=0.2, top=0.95)
    y_values = []
    for row in range(len(array2d)):
        y_values.append(int(array2d[row][target_col]) if array2d[row][target_col] != '' else None)
    axes.plot(times, y_values, label=header[target_col])
    if is_time_range_hour_option:
        axes.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0, 24, 12), tz=None))
        axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m/%d-%H:%M'))
    else:
        axes.xaxis.set_major_locator(mdates.DayLocator(bymonthday=None, interval=1, tz=None))
        axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m/%d'))
    axes.set_title(title)
    axes.set_xlabel('Time')
    axes.set_ylabel('Filesystem Usage [KB]')
    axes.set_ylim(bottom=0)
    axes.legend()
    axes.grid()
    plt.xticks(rotation=30)


def add_time_and_disk_usage_array2d(datetime: str, filesystems: List[str], filesystem_dict: Dict,
                                    df_array2d: List[List[str]]):
    if datetime == '':
        return
    record: List[str] = [''] * (len(filesystems) + 1)
    record[0] = datetime
    for filesystem_name in filesystem_dict.keys():
        record[filesystems.index(filesystem_name) + 1] = filesystem_dict[filesystem_name]
    df_array2d.append(record)  # array2d record : datetime + disk usage


def get_filesystem_and_total_size(lines: List[str], filesystems: List[str], filesystem_total_sizes: List[str]):
    block_count = 0
    for line in lines:
        if line.startswith(LOG_ONE_BLOCK_START_MARK):
            if block_count > 0:
                break
        if line.startswith(FILESYSTEM_FILTER_TOP_STRING):
            line_columns: List[str] = line.split()
            filesystems.append(line_columns[FILESYSTEM_INDEX])
            filesystem_total_sizes.append(line_columns[ONE_K_BLOCKS_INDEX])


def get_date_time_in_line(line: str) -> str:
    slice_line = line[LOG_ONE_BLOCK_START_LINE_SLICE_SIZE:]
    date_time = slice_line[:LOG_ONE_BLOCK_START_LINE_SLICE_SIZE]
    return date_time


def analyze_filesystem_data_line(line, filesystems: List[str], filesystem_dict: Dict):
    line_columns: List[str] = line.split()
    if line_columns[FILESYSTEM_INDEX] in filesystems:
        filesystem_dict[line_columns[FILESYSTEM_INDEX]] = line_columns[USED_INDEX]


def analyze_df_log_lines(lines: List[str], filter_start_time: Optional, filter_end_time: Optional,
                         filesystems: List[str], df_array2d: List[List[str]]):
    filesystem_dict: Dict = {}
    datetime = ''
    for line in lines:
        if not line:
            continue
        if line.startswith(LOG_ONE_BLOCK_START_MARK):
            # one block start line
            if is_contain_rage_from_start_to_end(datetime, filter_start_time, filter_end_time, DATE_TIME_FORMAT):
                add_time_and_disk_usage_array2d(datetime, filesystems, filesystem_dict, df_array2d)
            datetime = get_date_time_in_line(line)
        if line.startswith(FILESYSTEM_FILTER_TOP_STRING):
            analyze_filesystem_data_line(line, filesystems, filesystem_dict)
    if is_contain_rage_from_start_to_end(datetime, filter_start_time, filter_end_time, DATE_TIME_FORMAT):
        add_time_and_disk_usage_array2d(datetime, filesystems, filesystem_dict, df_array2d)


def analyze_df_logs(lines: List[str], is_time_range_hour_option, filter_start_time, filter_end_time):
    df_array2d: List[List[str]] = []
    filesystems: List[str] = []
    filesystem_total_sizes: List[str] = []
    get_filesystem_and_total_size(lines, filesystems, filesystem_total_sizes)
    analyze_df_log_lines(lines, filter_start_time, filter_end_time, filesystems, df_array2d)
    for index in range(len(filesystems)):
        view_line_graph(GRAPH_TITLE, filesystems, df_array2d, is_time_range_hour_option, index + 1)
    df_array2d.append(['TOTAL:'] + filesystem_total_sizes)
    df_array2d.append(['MAX:'] + create_max_value_row(df_array2d))
    df_array2d.append(['AVG:'] + create_average_value_row(df_array2d))
    write_csv_file(OUTPUT_FILE_NAME, filesystems, df_array2d)
    plt.show()


def main(args: List[str]):
    """

    :param args: command line arguments
    :return: void
    """
    is_view_graph = False
    is_time_range_hour_option = False
    filter_start_time: Optional = None
    filter_end_time: Optional = None
    if START_DATETIME_OPTION in args:
        filter_start_time = convert_option_date_time(START_DATETIME_OPTION, args)
    if END_DATETIME_OPTION in args:
        filter_end_time = convert_option_date_time(END_DATETIME_OPTION, args)
    if GRAPH_TIME_RANGE_HOUR_OPTION in args:
        is_time_range_hour_option = True
    file_paths: List[str] = glob.glob("../input/df_*.log")
    lines = []
    for file_path in file_paths:
        with open(file_path, 'r', encoding="utf-8_sig") as f:
            lines += f.readlines()
    analyze_df_logs(lines, is_time_range_hour_option, filter_start_time, filter_end_time)


main(sys.argv)
