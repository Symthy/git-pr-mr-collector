import glob
import sys
import matplotlib.pyplot as plt
from typing import Optional, List
from analyzeTool.analysis_util import convert_date_time, write_csv_file, except_out_of_start_to_end_filter_range, \
    create_max_value_row, create_average_value_row

GET_PARAM_NAME_START_INDEX = 3
AVAILABLE_NAME_INDEX = 7
DATE_INDEX = 0
TIME_INDEX = 1
AVAILABLE_VALUE_INDEX = 8
TOTAL_VALUE_INDEX = 3
GET_VALUE_START_INDEX = 4
LOG_START_LINE = 1
LOG_LINE_INCREMENT = 3
START_DATETIME_OPTION = '--startTime'
END_DATETIME_OPTION = '--endTime'
OUTPUT_FILE_NAME = 'free_result'


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
    times = [array2d[i][0] for i in range(len(array2d)) if i < len(array2d)]
    x_alias = [i for i in times[::int(len(times) / 10)]]
    fig, axes = plt.subplots()
    for col in range(len(array2d[0])):
        if col == 0:
            # skip because column 0 is time
            continue
        y_values = []
        for row in range(len(array2d)):
            y_values.append(int(array2d[row][col]) if array2d[row][col] != '' else None)
        axes.plot(times, y_values, label=header[col])
    axes.set_title(title)
    axes.set_xlabel('Time')
    axes.set_xticks(x_alias)
    axes.set_ylabel('Memory [KB]')
    axes.set_ylim(0, total)
    axes.legend()
    axes.grid()
    plt.xticks(rotation=30)


def analyze_free_log_lines(lines: List[str], free_array2d: List[List[str]]):
    line_counter: int = LOG_START_LINE
    while line_counter < len(lines):
        line_columns: List[str] = lines[line_counter].split()
        free_array2d.append(
            # [line_columns[DATE_INDEX] + ' ' + line_columns[TIME_INDEX]] + line_columns[GET_VALUE_START_INDEX:])
            [line_columns[DATE_INDEX] + ' ' + line_columns[TIME_INDEX]] + [line_columns[AVAILABLE_VALUE_INDEX]])
        line_counter += LOG_LINE_INCREMENT


def get_total_memory(line: str) -> int:
    return int(line.split()[TOTAL_VALUE_INDEX])


def analyze_free_params(line: str) -> List[str]:
    line_columns: List[str] = line.split()
    # return [line_columns[i] for i in range(len(line_columns)) if i >= GET_PARAM_NAME_START_INDEX]
    return [line_columns[AVAILABLE_NAME_INDEX]]


def analyze_free_log(file_path, is_output_excel, filter_start_time, filter_end_time):
    free_array2d: List[List[str]] = []
    with open(file_path, 'r', encoding="utf-8_sig") as f:
        lines = f.readlines()
    param_names: List[str] = [''] + analyze_free_params(lines[0])
    total: int = get_total_memory(lines[1])
    analyze_free_log_lines(lines, free_array2d)
    except_out_of_start_to_end_filter_range(filter_start_time, filter_end_time, param_names, free_array2d)
    view_line_graph('Free Memory', total, param_names, free_array2d)
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
        try:
            filter_start_time = convert_date_time(START_DATETIME_OPTION, args)
        except Exception:
            print('invalid --startTime format (YYYY-mm-dd HH:MM:SS)')
            raise
    if END_DATETIME_OPTION in args:
        try:
            filter_end_time = convert_date_time(END_DATETIME_OPTION, args)
        except Exception:
            print('invalid --endTime format (YYYY-mm-dd HH:MM:SS)')
            raise
    file_paths: List[str] = glob.glob("../input/free_*.log")
    for file_path in file_paths:
        analyze_free_log(file_path, is_output_excel, filter_start_time, filter_end_time)


main(sys.argv)
