import sys
import csv
from typing import List, Dict

PID_INDEX = 0
CPU_INDEX = 8
MEM_INDEX = 9
COMMAND_INDEX = 11
PID_VALUE_COLUMN_COUNT = 12
FILTER_VALUE = 1.0


def create_max_value_order(str_max_values: List[str]):
    max_values: List[float] = list(map(lambda s: float(s), str_max_values))
    sorted_max_values = sorted(max_values, reverse=True)
    max_order_indexes: List[int] = [max_values.index(v) + 1 for v in sorted_max_values]
    return [0] + max_order_indexes


def create_max_value_per_pid(array2d: List[List[str]]):
    rows_num: int = len(array2d)
    columns_num: int = len(array2d[0])
    max_values: List[str] = []
    for j in range(columns_num):
        if j == 0:
            continue
        max = '0.0'
        for i in range(rows_num):
            if array2d[i][j] != '' and float(max) < float(array2d[i][j]):
                max = array2d[i][j]
        max_values.append(max)
    return max_values


def pack_empty_str(pid_count: int, array2d: List[List[str]]):
    for record in array2d:
        diff = pid_count - (len(record) - 1)  # array2d row : time + pids
        record.extend([''] * diff)


def write_csv_file(pids: List[str], array2d: List[List[str]]):
    pack_empty_str(len(pids), array2d)
    max_values_per_pid: List[str] = create_max_value_per_pid(array2d)
    max_order_indexes: List[int] = create_max_value_order(max_values_per_pid)

    header = [''] + pids
    array2d.append(['MAX:'] + max_values_per_pid)
    with open('../output/top.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, lineterminator='\n')
        writer.writerow(header)
        # writer.writerows(array2d)
        for row in range(len(array2d)):
            writer.writerow([array2d[row][index] for index in max_order_indexes])


def add_time_and_value_array2d(time: str, pids: List[str], mem_dict: Dict, array2d: List[List[str]]):
    if time == '' or len(mem_dict) == 0:
        return
    record: List[str] = [''] * (len(pids) + 1)
    record[0] = time
    for pid_key in mem_dict.keys():
        record[pids.index(pid_key) + 1] = mem_dict[pid_key]
    array2d.append(record)


def analyze_pid_value_line(line: str, pids: List[str], mem_dict: Dict):
    line_columns: List[str] = line.split()
    pid: str = line_columns[PID_INDEX] + '(' + line_columns[COMMAND_INDEX] + ')'
    mem: str = line_columns[MEM_INDEX]
    if float(mem) >= FILTER_VALUE:
        if pid not in pids:
            pids.append(pid)
        mem_dict[pid] = mem


def analyze_top_log_lines(lines: List[str]):
    is_pid_value_block = False
    pids: List[str] = []
    time_mem_array2d: List[List[str]] = []
    mem_dict: Dict = {}
    time = ''
    for line in lines:
        line_columns = line.split();
        if line.startswith('top -'):
            add_time_and_value_array2d(time, pids, mem_dict, time_mem_array2d)
            time = line_columns[2]
            is_pid_value_block = False
            mem_dict = {}
            continue
        if line.startswith('    PID'):
            is_pid_value_block = True
            continue
        if is_pid_value_block and len(line_columns) == PID_VALUE_COLUMN_COUNT:
            analyze_pid_value_line(line, pids, mem_dict)
    add_time_and_value_array2d(time, pids, mem_dict, time_mem_array2d)
    write_csv_file(pids, time_mem_array2d)


def analyze_top_log(file_path: str):
    with open(file_path, 'r') as f:
        lines = f.readlines()
        analyze_top_log_lines(lines)


def main(args: List[str]):
    file_paths = [sys.argv[i] for i in range(len(args)) if i != 0]
    for file_path in file_paths:
        analyze_top_log(file_path)


args: List[str] = sys.argv
main(args)
