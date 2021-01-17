import datetime as dt
import glob
import re
import sys
from typing import List, Optional

from analyzeTool.analysis_util import write_csv_file

OUTPUT_FILE_NAME = 'log_wrap_result'


def get_date_time(line: str, format_num: int) -> Optional[dt]:
    time = None
    try:
        if format_num == 1:
            m = re.match(r'\d{4}年\d{2}月\d{2}日 \d{2}時\d{2}分\d{2}秒', line)
            time = dt.datetime.strptime(m.group(), '%Y年%m月%d日 %H時%M分%S秒')
        else:
            return None
    except Exception:
        print('Fail get date time')
        return None
    return time


def analyze_time_logs(lines: List[str], result: List, format_num: int):
    last_row = len(lines)
    startTime: Optional[dt] = get_date_time(lines[0], format_num)
    endTime: Optional[dt] = get_date_time(lines[last_row], format_num)
    if startTime is not None or endTime is not None:
        td = endTime - startTime
        result.append([startTime, endTime, td.total_seconds()])


def main(args: List[str]):
    file_paths: List[str] = glob.glob("../input/*.log")
    result = ['start', 'end', 'diff']
    for file_path in file_paths:
        with open(file_path, 'r', encoding="utf-8_sig") as f:
            lines = f.readlines()
            analyze_time_logs(lines, result, int(args[0]))
    write_csv_file(result)


main(sys.argv)
