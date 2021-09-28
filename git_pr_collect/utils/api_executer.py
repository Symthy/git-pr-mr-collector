from typing import Callable, List

import requests


def execute_get_api(url: str, headers: object) -> List:
    response = requests.get(url, headers=headers)
    print(response.status_code, response.reason, url)
    if response.status_code == 200:
        response_json = response.json()
        return response_json if isinstance(response_json, list) else [response_json]
    return []


def retry_execute_git_api(api_execute_func: Callable[[int, any], int], *args):
    is_retry = True
    page_count = 1
    while is_retry:
        count = api_execute_func(page_count, args[0] if len(args) != 0 else None)
        page_count += 1
        is_retry = False if count < 100 else True
