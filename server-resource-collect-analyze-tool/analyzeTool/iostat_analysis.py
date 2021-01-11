import datetime as dt
import glob
import re
import sys
from typing import List, Optional, Dict

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from analyzeTool.analysis_util import convert_option_date_time, write_csv_file, \
    create_max_value_row, create_average_value_row, is_contain_rage_from_start_to_end, convert_date_time

R_PER_S_INDEX = 1  # r/s index
W_PER_S_INDEX = 7  # w/s index
DEV_PARTITION_NAME_INDEX = 0  # Device Partition Name index
IOSTAT_READ_IO_FILE_NAME = 'iostat_read_result'
IOSTAT_WRITE_IO_FILE_NAME = 'iostat_write_result'
EXCEL_OPTION = '--withExcel'
START_DATETIME_OPTION = '--startTime'
END_DATETIME_OPTION = '--endTime'


def view_line_graph(dev_partition_names: List[str], read_iops_array2d: List[List[str]],
                    write_iops_array2d: List[List[str]]):
    """
    Description:
        create and view line graph by matplotlib.
    :param dev_partition_names: top line of output file. top line is '' and device partition name.
    :param read_iops_array2d: 2d array (row: date time, column: process). row 0 is date time.
    :param write_iops_array2d: 2d array (row: date time, column: process). row 0 is date time.
    :return: void
    """
    def plot_graph(ax, graph_title: str, times: List[str], header: List[str], array2d: List[List[str]]):
        for col in range(len(array2d[0])):
            if col == 0:
                # skip because column 0 is time
                continue
            y_values = []
            for row in range(len(array2d)):
                y_values.append(float(array2d[row][col]) if array2d[row][col] != '' else None)
            ax.plot(times, y_values, label=header[col])
        ax.set_title(graph_title)
        ax.set_xlabel('Time')
        ax.set_ylabel('IOPS')
        ax.legend()
        ax.grid()
    times = [convert_date_time(write_iops_array2d[i][0]) for i in range(len(write_iops_array2d))]
    x_alias = [time for time in times[::int(len(times) / 10)]]
    fig, (ax_top, ax_under) = plt.subplots(nrows=2, ncols=1, sharex=True)
    fig.subplots_adjust(bottom=0.2, top=0.95)
    plot_graph(ax_top, 'IO read (r/s)', times, dev_partition_names, read_iops_array2d)
    plot_graph(ax_under, 'IO write (w/s)', times, dev_partition_names, write_iops_array2d)
    ax_under.xaxis.set_major_locator(mdates.DayLocator(bymonthday=None, interval=1, tz=None))
    ax_under.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m/%d'))
    plt.xticks(rotation=30)
    plt.subplots_adjust(hspace=0.3)


def analyze_iostat_extend_dev_log_one_line(line_columns: List[str], dev_partition_names: List[str],
                                           read_iops_dict: Dict, write_iops_dict: Dict,
                                           is_got_dev_partition_name: bool):
    dev_partition_name = line_columns[DEV_PARTITION_NAME_INDEX]
    if not is_got_dev_partition_name:
        dev_partition_names.append(dev_partition_name)
    read_iops_dict[dev_partition_name] = line_columns[R_PER_S_INDEX]
    write_iops_dict[dev_partition_name] = line_columns[W_PER_S_INDEX]


def add_time_iops_array2d(date_time: str, dev_partition_names: List[str], iops_dict: Dict,
                          iops_array2d: List[List[str]]):
    if date_time == '':
        return
    record: List[str] = [''] * len(dev_partition_names)
    for name in dev_partition_names:
        record[dev_partition_names.index(name)] = iops_dict[name]
    iops_array2d.append([date_time] + record)


def get_date_time(line: str) -> str:
    return dt.datetime.strptime(line[:-1], '%Y年%m月%d日 %H時%M分%S秒').strftime('%Y/%m/%d %H:%M:%S')


def is_date_time_line(line: str) -> bool:
    result = re.match(r'\d{4}年\d{2}月\d{2}日 \d{2}時\d{2}分\d{2}秒', line)
    if result:
        return True
    return False


def analyze_iostat_log_lines(lines: List[str], filter_start_time: Optional, filter_end_time: Optional,
                             dev_partition_names: List[str], read_iops_array2d: List[List[str]],
                             write_iops_array2d: List[List[str]]):
    is_got_dev_partition_name = False
    date_time: str = ''
    read_iops_dict: Dict = {}
    write_iops_dict: Dict = {}
    one_block_line_count: int = 0
    for line in lines:
        if is_date_time_line(line):
            if is_contain_rage_from_start_to_end(date_time, filter_start_time, filter_end_time):
                add_time_iops_array2d(date_time, dev_partition_names, read_iops_dict, read_iops_array2d)
                add_time_iops_array2d(date_time, dev_partition_names, write_iops_dict, write_iops_array2d)
            if one_block_line_count != 0 and not is_got_dev_partition_name:
                is_got_dev_partition_name = True
            one_block_line_count = 0
            date_time = get_date_time(line)
            read_iops_dict = {}
            write_iops_dict = {}
            continue
        line_columns = line.split()
        if len(line_columns) == 21:
            if one_block_line_count == 0:
                one_block_line_count += 1
                continue
            analyze_iostat_extend_dev_log_one_line(line_columns, dev_partition_names, read_iops_dict, write_iops_dict,
                                                   is_got_dev_partition_name)
            one_block_line_count += 1
    if is_contain_rage_from_start_to_end(date_time, filter_start_time, filter_end_time):
        add_time_iops_array2d(date_time, dev_partition_names, read_iops_dict, read_iops_array2d)
        add_time_iops_array2d(date_time, dev_partition_names, write_iops_dict, write_iops_array2d)


def analyze_iostat_log(lines, is_output_excel, is_view_graph, filter_start_time, filter_end_time):
    dev_partition_names: List[str] = []
    read_iops_array2d: List[List[str]] = []
    write_iops_array2d: List[List[str]] = []
    analyze_iostat_log_lines(lines, filter_start_time, filter_end_time, dev_partition_names, read_iops_array2d,
                             write_iops_array2d)
    dev_partition_names = [''] + dev_partition_names
    view_line_graph(dev_partition_names, read_iops_array2d, write_iops_array2d)
    read_iops_array2d.append(['MAX:'] + create_max_value_row(read_iops_array2d))
    read_iops_array2d.append(['AVG:'] + create_average_value_row(read_iops_array2d))
    write_iops_array2d.append(['MAX:'] + create_max_value_row(write_iops_array2d))
    write_iops_array2d.append(['AVG:'] + create_average_value_row(write_iops_array2d))
    write_csv_file(IOSTAT_READ_IO_FILE_NAME, dev_partition_names, read_iops_array2d)
    write_csv_file(IOSTAT_WRITE_IO_FILE_NAME, dev_partition_names, write_iops_array2d)
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
    file_paths: List[str] = glob.glob("../input/iostat_x_dev_*.log")
    lines = []
    for file_path in file_paths:
        with open(file_path, 'r', encoding="utf-8_sig") as f:
            lines += f.readlines()
    analyze_iostat_log(lines, is_output_excel, is_view_graph, filter_start_time, filter_end_time)


main(sys.argv)
