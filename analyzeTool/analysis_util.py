import csv
from typing import List, Optional
import datetime as dt


def write_csv_file(filename: str, header: List[str], array2d: List[List[str]]):
    """
    Description:
        output csv file (row: date time, column: process)
    :param filename: output file name.
    :param header: top line of output file. top line is '' and process id.
    :param array2d: 2d array (row: date time, column: process). row 0 is date time.
    :return: void
    """
    with open('../output/' + filename + '.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, lineterminator='\n')
        writer.writerow(header)
        writer.writerows(array2d)


def convert_date_time(option: str, args: List[str]):
    """
    Description:
        convert date time from command line input
    :param option: option name
    :param args: command line arguments
    :return: void
    """
    if not option in args:
        return None
    index = args.index(option)
    if len(args) > index:
        filter_start_time = args[index + 1]
        try:
            return dt.datetime.strptime(filter_start_time, '%Y/%m/%d %H:%M:%S')
        except Exception:
            raise


def except_out_of_start_to_end_filter_range(filter_start_time: Optional, filter_end_time: Optional,
                                            header: List[str], array2d: List[List[str]]):
    """
    Description:
        except out of start date time to end date time range
    :param filter_start_time: output to start date time.
    :param filter_end_time: output to end date time.
    :param header: header list. first is ''.
    :param array2d: 0 row is date time.
    :return: void
    """
    if filter_start_time is None and filter_end_time is None:
        return
    # remove out of start to end range
    for row in reversed(range(len(array2d))):
        date_time: dt = dt.datetime.strptime(array2d[row][0], '%Y/%m/%d %H:%M:%S')
        if filter_start_time is not None and date_time < filter_start_time:
            del (array2d[row])
        if filter_end_time is not None and date_time > filter_end_time:
            del (array2d[row])
    # remove all empty column
    delete_column_indexes = []
    for col in reversed(range(len(array2d[0]))):
        is_empty_column = True
        for row in range(len(array2d)):
            if array2d[row][col] != '':
                is_empty_column = False
                break
        if is_empty_column:
            delete_column_indexes.append(col)
    for col in delete_column_indexes:
        del (header[col])
        for row in reversed(range(len(array2d))):
            del (array2d[row][col])


def create_max_value_row(array2d: List[List[str]]) -> List[str]:
    """
    Description:
        create max value list per process id.
    :param array2d: 2d array (row: date time, column: process). row 0 is date time.
    :return: max value list per process id.
    """
    rows_len: int = len(array2d)
    columns_len: int = len(array2d[0])
    max_values: List[str] = []
    for col in range(columns_len):
        if col == 0:
            continue
        max = '0.0'
        for row in range(rows_len):
            if array2d[row][col] != '' and float(max) < float(array2d[row][col]):
                max = array2d[row][col]
        max_values.append(max)
    return max_values
