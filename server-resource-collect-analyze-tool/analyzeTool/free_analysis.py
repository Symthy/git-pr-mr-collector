import glob
import sys
from typing import Optional, List

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from analyzeTool.analysis_util import convert_option_date_time, write_csv_file, \
    create_max_value_row, create_average_value_row, is_contain_rage_from_start_to_end, convert_date_time

GET_PARAM_NAME_START_INDEX = 3
AVAILABLE_NAME_INDEX = 7
DATE_INDEX = 0
TIME_INDEX = 1
TOTAL_VALUE_INDEX = 3
USED_VALUE_INDEX = 4
FREE_VALUE_INDEX = 5
SHARED_VALUE_INDEX = 6
BUFF_CACHE_VALUE_INDEX = 7
AVAILABLE_VALUE_INDEX = 8

# Variables
GET_VALUE_START_INDEX = 4
GRAPH_TITLE = 'Memory Usage'
START_DATETIME_OPTION = '--startTime'
END_DATETIME_OPTION = '--endTime'
OUTPUT_FILE_NAME = 'free_result'
MEM_LABEL = 'Mem:'
SWAP_LABEL = 'Swap:'
LABEL_INDEX = 2


def view_line_graph(title: str, total: int, header: List[str], array2d: List[List[str]]):
    """
    Description:
        create and view line graph by matplotlib.
    :param total: memory total value
    :param title: graph title.
    :param header: top line of output file. top line is '' and process id.
    :param array2d: 2d array (row: date time, column: process). row 0 is date time.
    :return: void
    """
    times = [convert_date_time(array2d[i][0]) for i in range(len(array2d)) if i < len(array2d)]
    fig, axes = plt.subplots()
    fig.subplots_adjust(bottom=0.2, top=0.95)
    for col in range(len(array2d[0])):
        if col != 6:
            # skip because column 0 is time and view memory usage only
            continue
        y_values = []
        for row in range(len(array2d)):
            y_values.append(int(array2d[row][col]) if array2d[row][col] != '' else None)
        axes.plot(times, y_values, label=header[col])
    axes.xaxis.set_major_locator(mdates.DayLocator(bymonthday=None, interval=1, tz=None))
    # axes.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0, 24, 12), tz=None))
    axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m/%d'))
    axes.set_title(title)
    axes.set_xlabel('Time')
    axes.set_ylabel('Memory [KB]')
    axes.set_ylim(0, total)
    axes.legend()
    axes.grid()
    plt.xticks(rotation=30)


def analyze_free_log_lines(lines: List[str], total: int, filter_start_time: Optional, filter_end_time: Optional,
                           free_array2d: List[List[str]]):
    array = []
    for line in lines:
        line_columns: List[str] = line.split()
        datetime = line_columns[0] + ' ' + line_columns[1]
        if not is_contain_rage_from_start_to_end(datetime, filter_start_time, filter_end_time):
            array = []
            continue
        if line_columns[LABEL_INDEX] == MEM_LABEL:
            used = line_columns[USED_VALUE_INDEX]
            free = line_columns[FREE_VALUE_INDEX]
            shared = line_columns[SHARED_VALUE_INDEX]
            buffcache = line_columns[BUFF_CACHE_VALUE_INDEX]
            available = line_columns[AVAILABLE_VALUE_INDEX]
            use_memory = str(total - int(available))
            array = [line_columns[DATE_INDEX] + ' ' + line_columns[TIME_INDEX]] + [used] + [free] + [shared] + [
                buffcache] + [available] + [use_memory]
        if line_columns[LABEL_INDEX] == SWAP_LABEL:
            used = line_columns[USED_VALUE_INDEX]
            free = line_columns[FREE_VALUE_INDEX]
            array.append(used)
            array.append(free)
            free_array2d.append(array)
            array = []


def get_total_memory(lines: List[str]) -> int:
    for line in lines:
        columns = line.split()
        if columns[LABEL_INDEX] == MEM_LABEL:
            return int(columns[TOTAL_VALUE_INDEX])
    raise ValueError('Not Found "MEM:" in free log')


def analyze_free_params(line: str) -> List[str]:
    # line_columns: List[str] = line.split()
    # return [line_columns[i] for i in range(len(line_columns)) if i >= GET_PARAM_NAME_START_INDEX]
    return ['mem used'] + ['mem free'] + ['mem shared'] + ['mem buff/cache'] + ['available'] + ['Memory Usage'] + [
        'swap used'] + ['swap free']


def analyze_free_logs(lines: List[str], is_output_excel, filter_start_time, filter_end_time):
    free_array2d: List[List[str]] = []
    param_names: List[str] = [''] + analyze_free_params(lines[0])
    total: int = get_total_memory(lines)
    analyze_free_log_lines(lines, total, filter_start_time, filter_end_time, free_array2d)
    view_line_graph(GRAPH_TITLE, total, param_names, free_array2d)
    free_array2d.append(['MAX:'] + create_max_value_row(free_array2d))
    free_array2d.append(['AVG:'] + create_average_value_row(free_array2d))
    write_csv_file(OUTPUT_FILE_NAME, param_names, free_array2d)
    plt.show()


def main(args: List[str]):
    """

    :param args: command line arguments
    :return: void
    """
    is_output_excel = False
    is_view_graph = False
    filter_start_time: Optional = None
    filter_end_time: Optional = None
    if START_DATETIME_OPTION in args:
        filter_start_time = convert_option_date_time(START_DATETIME_OPTION, args)
    if END_DATETIME_OPTION in args:
        filter_end_time = convert_option_date_time(END_DATETIME_OPTION, args)
    file_paths: List[str] = glob.glob("../input/free_*.log")
    lines = []
    for file_path in file_paths:
        with open(file_path, 'r', encoding="utf-8_sig") as f:
            lines += f.readlines()
    analyze_free_logs(lines, is_output_excel, filter_start_time, filter_end_time)


main(sys.argv)
