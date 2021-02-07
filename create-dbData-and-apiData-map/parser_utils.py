from typing import Dict, List


def get_target_from_json(json_data: Dict, path_list: List[str]):
    parent_data = json_data
    child_data = None
    for path in path_list:
        child_data = parent_data[path]
        parent_data = child_data
    return child_data
