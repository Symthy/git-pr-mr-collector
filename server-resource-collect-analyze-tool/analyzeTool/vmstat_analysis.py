import glob
import sys
from typing import Optional, List

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from analyzeTool.analysis_util import convert_option_date_time, write_csv_file, \
    create_max_value_row, create_average_value_row, is_contain_rage_from_start_to_end, convert_date_time

# Constant Value
DATE_INDEX = 0
TIME_INDEX = 1
PROCESS_RUN_INDEX = 2
MEMORY_FREE_INDEX = 5
IO_BLOCK_IN_INDEX = 10
IO_BLOCK_OUT_INDEX = 11
CPU_USE_INDEX = 14
LOG_START_LINE = 2
LOG_LINE_INCREMENT = 3

# Variables
START_DATETIME_OPTION = '--startTime'
END_DATETIME_OPTION = '--endTime'
OUTPUT_FILE_NAME = 'vmstat_result'
HEADER_LABELS = ['proc_run', 'mem_free', 'io_bi', 'io_bo', 'cpu_use']
CPU_USE_INDEX = 4
GRAPH_TITLE = 'CPU Usage'


def view_line_graph_cpu_use(title: str, array2d: List[List[str]]):
    """
    Description:
        create and view line graph by matplotlib.
    :param title: graph title.
    :param array2d: 2d array (row: date time, column: process). row 0 is date time.
    :return: void
    """
    times = [convert_date_time(array2d[i][0]) for i in range(len(array2d)) if i < len(array2d)]
    fig, axes = plt.subplots()
    fig.subplots_adjust(bottom=0.2, top=0.95)
    for col in range(len(array2d[0])):
        if col != CPU_USE_INDEX:
            # skip because column 0 is time and view memory usage only
            continue
        y_values = []
        for row in range(len(array2d)):
            y_values.append(int(array2d[row][col]) if array2d[row][col] != '' else None)
        axes.plot(times, y_values, label=HEADER_LABELS[CPU_USE_INDEX])
    axes.xaxis.set_major_locator(mdates.DayLocator(bymonthday=None, interval=1, tz=None))
    axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m/%d'))
    axes.set_title(title)
    axes.set_xlabel('Time')
    axes.set_ylabel('CPU Usage [%]')
    axes.set_ylim(0, 100)
    axes.legend()
    axes.grid()
    plt.xticks(rotation=30)


def analyze_vmstat_log_lines(lines: List[str], filter_start_time: Optional, filter_end_time: Optional,
                             array2d: List[List[str]]):
    line_counter: int = LOG_START_LINE
    while line_counter < len(lines):
        line_columns: List[str] = lines[line_counter].split()
        datetime = line_columns[0] + ' ' + line_columns[1]
        if is_contain_rage_from_start_to_end(datetime, filter_start_time, filter_end_time):
            array2d.append(
                [line_columns[DATE_INDEX] + ' ' + line_columns[TIME_INDEX]] + [line_columns[PROCESS_RUN_INDEX]] + [
                    line_columns[MEMORY_FREE_INDEX]] + [line_columns[IO_BLOCK_IN_INDEX]] + [
                    line_columns[IO_BLOCK_OUT_INDEX]] + [line_columns[CPU_USE_INDEX]])
        line_counter += LOG_LINE_INCREMENT


def analyze_vmstat_log(lines: List[str], is_output_excel: bool, filter_start_time: Optional, filter_end_time: Optional):
    vmstat_array2d: List[List[str]] = []
    analyze_vmstat_log_lines(lines, filter_start_time, filter_end_time, vmstat_array2d)
    header_labels = [''] + HEADER_LABELS
    view_line_graph_cpu_use(GRAPH_TITLE, vmstat_array2d)
    vmstat_array2d.append(['MAX:'] + create_max_value_row(vmstat_array2d))
    vmstat_array2d.append(['AVG:'] + create_average_value_row(vmstat_array2d))
    write_csv_file(OUTPUT_FILE_NAME, header_labels, vmstat_array2d)
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
    file_paths: List[str] = glob.glob("../input/vmstat_*.log")
    lines: List[str] = []
    for file_path in file_paths:
        with open(file_path, 'r', encoding="utf-8_sig") as f:
            lines += f.readlines()
    analyze_vmstat_log(lines, is_output_excel, filter_start_time, filter_end_time)


main(sys.argv)
