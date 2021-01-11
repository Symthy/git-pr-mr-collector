import json
import os
from datetime import datetime
import time
from typing import List

# constant value
JSON_FOLDER_PATH = 'measurement'  # measurement def json path
MEASUREMENT_KEY = 'measurement'
START_TIMESTAMP_KEY = 'startTimestamp'
TAG_KEY = 'tags'
FIELD_KEY = 'fields'
KEY_NAME_KEY = 'keyName'
BASE_VALUE_KEY = 'baseValue'
VALUE_TYPE_KEY = 'valueType'
VALUE_TYPE_FIXED = 'fixed'
VALUE_TYPE_RANDOM = 'random'
RANDOM_COEFFICIENT = 0
CREATE_LINE_NUM_KEY = 'createLineNum'
INCREMENT_TIME_KEY = 'incrementTimeMinutesPerLine'


def create_key_value_str(key_value_dict: dict) -> str:
    key_value_str: str = ''
    count: int = 1
    for key, value in key_value_dict.items():
        key_value_str += key + '=' + str(value)
        if count >= len(key_value_dict):
            break
        key_value_str += ','
        count += 1
    return key_value_str


def create_insert_query(measurement_name: str, tags_dict: dict, fields_dict: dict, unix_nano_sec: int) -> str:
    """
    create influx db insert query one line
    insert query format:
        <measurement>[,<tag-key>=<tag-value>...] <field-key>=<field-value>[,<field2-key>=<field2-value>...] [unix-nano-timestamp]
    """
    # print(measurement_name, tags_dict, fields_dict, unix_nano_sec)
    insert_query: str = 'INSERT ' + measurement_name
    if len(tags_dict) > 0:
        insert_query += ','
        insert_query += create_key_value_str(tags_dict)
    insert_query += ' '
    insert_query += create_key_value_str(fields_dict)
    insert_query += ' '
    insert_query += str(unix_nano_sec)
    return insert_query


def create_key_value_dict(configs: List) -> dict:
    key_value_map = {}
    for i in range(len(configs)):
        config = configs[i]
        key_name = config[KEY_NAME_KEY]
        # if config[VALUE_TYPE_KEY] == VALUE_TYPE_FIXED:
        base_value = config[BASE_VALUE_KEY]
        key_value_map[key_name] = base_value
    return key_value_map


def create_insert_query_lines(measurement_name: str, start_unix_nano_sec: int, tag_configs: List, field_configs: List,
                              create_line_num: int, increment_minutes_per_line: int) -> List[str]:
    query_lines: List = []
    for i in range(create_line_num):
        tags_dict: dict = create_key_value_dict(tag_configs)
        fields_dict: dict = create_key_value_dict(field_configs)
        unix_nano_sec = start_unix_nano_sec + increment_minutes_per_line * (i + 1) * 60 * 1000 * 1000
        query_lines.append(create_insert_query(measurement_name, tags_dict, fields_dict, unix_nano_sec))
    return query_lines


# get json file list
json_files = [json_file for json_file in os.listdir(JSON_FOLDER_PATH) if json_file.endswith('.json')]

for json_file in json_files:
    json_open = open(JSON_FOLDER_PATH + '/' + json_file, 'r')
    json_data = json.load(json_open)

    measurement_name: str = ''
    start_unix_nano_sec: int = 0
    tag_configs: List = []
    field_configs: List = []
    create_line_num: int = 0
    increment_minutes_per_line: int = 0

    for key, value in json_data.items():

        if key == MEASUREMENT_KEY:
            measurement_name = value
        if key == START_TIMESTAMP_KEY:
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            # convert datetime to unix milli sec
            start_unix_nano_sec = int(time.mktime(dt.timetuple())) * 1000 * 1000
        if key == TAG_KEY:
            tag_configs = value
        if key == FIELD_KEY:
            field_configs = value
        if key == CREATE_LINE_NUM_KEY:
            create_line_num = value
        if key == INCREMENT_TIME_KEY:
            increment_minutes_per_line = value

    insert_query_lines = create_insert_query_lines(measurement_name, start_unix_nano_sec, tag_configs, field_configs,
                                                   create_line_num, increment_minutes_per_line)
    # output
    for query in insert_query_lines:
        print(query)
