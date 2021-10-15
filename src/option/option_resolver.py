from typing import List

from exception.error import OptionValueError


def resolve_repository_option_value(option_name_repository: str, option_name_pr: str, command_args: List[str]) -> str:
    if not option_name_repository in command_args:
        return ""
    repository_option_index = command_args.index(option_name_repository)
    if len(command_args) == repository_option_index + 1 or command_args[repository_option_index + 1] == option_name_pr:
        print(f'[Warning] Invalid {option_name_repository} option value. Use config file value.')
        return ""
    return command_args[repository_option_index + 1]


def resolve_pr_option_value(option_name_pr: str, options: List[str], command_args: List[str]) -> List:
    pr_option_index = command_args.index(option_name_pr)
    if len(command_args) == pr_option_index + 1:
        # case: nothing option value
        raise OptionValueError()
    target_pr_ids = []
    for arg in command_args[pr_option_index + 1:]:
        if arg in options:
            # case: invalid value after other option
            break
        try:
            target_pr_ids.append(int(arg))
        except ValueError:
            # case: no number
            print(f'[Warning] invalid {option_name_pr} option value: {arg} is skip')
            continue
    if len(target_pr_ids) == 0:
        raise OptionValueError()
    return target_pr_ids
