import json
from typing import List, Dict

import sqlparse
from sqlparse.sql import TokenList, Token, Function, Identifier, IdentifierList, Parenthesis, Operation, Statement
from sqlparse.tokens import DML, Keyword, Name

from parser_utils import get_target_from_json


def sql_parser(json_data: Dict, sql_path: List[str]) -> List[Dict[str, List[str]]]:
    print('sql_parser():')  # debug

    def filter_identifier_list(tkn_list: TokenList, token: Token):
        # debug: pprint(token)
        index = tkn_list.token_index(token)
        prev_token: Token = tkn_list.token_prev(index)[1]
        if prev_token is not None:
            # prev is not exist(index: 0) -> None
            if not prev_token.match(DML, 'SELECT'):
                return False
        next_token: Token = tkn_list.token_next(index)[1]
        if next_token is not None:
            # next is not exist(index: list len max) -> None
            if not next_token.match(Keyword, 'FROM'):
                return False
        return True

    def sql_tokens_inner_function_parser(tokens: List) -> List[str]:
        field_names = []
        print('  sql_tokens_inner_function_parser():' + str(tokens))  # debug
        # pprint(tokens)
        for token in tokens:
            # debug: print(token.ttype)
            if token.ttype is Name:
                field_names.append(token.value)
                continue
            if type(token) is Function:
                # Identifier and Parenthesis in Function. exclude Identifier
                tokens_exclude_identifier = [t for t in token.tokens if type(t) is not Identifier]
                field_names.extend(sql_tokens_inner_function_parser(tokens_exclude_identifier))
                continue
            if type(token) is Parenthesis or type(token) is IdentifierList or type(
                    token) is Operation or type(token) is Identifier:
                field_names.extend(sql_tokens_inner_function_parser(token.tokens))
        # debug: print('inner func part:' + str(field_names))
        return field_names

    def sql_identifiers_parser(identifiers: List[Identifier]) -> Dict[str, List[str]]:
        field_map: Dict = {}
        for idn in identifiers:
            tokens: List = idn.tokens
            print('sql_identifiers_parser() target tokens:' + str(tokens))  # debug
            if len(tokens) == 1:
                field_map[tokens[0].value] = [tokens[0].value]
                continue
            fp_tokens = [t for t in tokens if type(t) is Function or type(t) is Parenthesis or type(t) is Operation]
            if len(fp_tokens) > 0:
                # Function or Parenthesis case
                field_map[tokens[len(tokens) - 1].value] = sql_tokens_inner_function_parser(fp_tokens)
                continue
            field_map[tokens[len(tokens) - 1].value] = [tokens[0].value]
        return field_map

    def sql_identifier_list_parser(idn_lists: List[IdentifierList]) -> List[Dict[str, List[str]]]:
        field_map_list: List[Dict] = []
        for identifier_list in idn_lists:
            # remove comma and whitespace
            identifiers: List[Identifier] = [token for token in identifier_list.tokens if type(token) is Identifier]
            field_map_list.append(sql_identifiers_parser(identifiers))
        return field_map_list

    json_sql = get_target_from_json(json_data, sql_path)
    statements: List[Statement] = sqlparse.parse(json_sql)
    token_list: TokenList = statements[0]
    identifier_lists: List[IdentifierList] = list(
        filter(lambda token: filter_identifier_list(token_list, token), token_list.tokens))
    print(identifier_lists)  # SELECT と FROM の間のデータ
    result = sql_identifier_list_parser(identifier_lists)
    print('sql parser result: ' + str(result))  # debug
    return result


def main():
    json_sql_path = ['sql']
    with open("input/definition.json", mode="r") as f:
        def_json_data = json.load(f)
    sql_parser(def_json_data, json_sql_path)


main()
