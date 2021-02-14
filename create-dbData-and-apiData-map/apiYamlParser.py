from typing import Dict, List, Any, Union, Hashable, ItemsView

import yaml

HTTP_METHOD_GET = 'get'
PATHS_KEY = 'paths'
RESPONSES_KEY = 'responses'
STATUS_200_KEY = '200'
SCHEMA_KEY = 'schema'
# definitions keys
DEFINITIONS_KEY = 'definitions'
PROPERTIES_KEY = 'properties'
ENUM_KEY = 'enum'
DEFINITIONS_HEADER = f'#/{DEFINITIONS_KEY}/'
# common keys
REF_KEY = '$ref'
ITEMS_KEY = 'items'
TYPE_KEY = 'type'


def definitions_parser(definitions_data: Dict) -> Dict[str, List[Dict[str, str]]]:
    def replace_definition(def_dict: Dict[str, List[Union[Dict[str, str], str]]], target_definition_name: str,
                           replace_target_fields: List[Union[Dict[str, str], str]]) -> List[Dict[str, str]]:
        """
        :param def_dict:
        :param target_definition_name: example -> User
        :param replace_target_fields: example -> [{'field': 'id', 'type': 'integer'}, {'field': 'name', 'type': 'string'}]
        :return:
        """
        replaced_definition_list = []
        for field_data in replace_target_fields:
            """
            field_data:
            {'field': 'id', 'type': 'integer'} or '#/definitions/Category'
            """
            if type(field_data) is str:
                # field_data is str
                target_def_name = field_data
                def_name: str = target_def_name[len(DEFINITIONS_HEADER):]
                replaced_def_list = replace_definition(def_dict, def_name, def_dict[target_def_name])
                for replaced_def_dict in replaced_def_list:
                    # add parent definition name in field name
                    field_name = target_definition_name + '.' + replaced_def_dict['field']
                    replaced_def_dict['field'] = field_name
                    replaced_definition_list.append(replaced_def_dict)
            # field_data is Dict
            def_name = target_definition_name + '.' + field_data['field']
            field_data['field'] = def_name
            replaced_definition_list.append(field_data)
        return replaced_definition_list

    def replace_definitions(def_dict: Dict[str, List[Union[Dict[str, str], str]]]) -> Dict[str, List[Dict[str, str]]]:
        """
        :param def_dict: {'#/definitions/Pet': [{'field': 'id', 'type': 'integer'}, '#/definitions/Category', {'field': 'name', 'type': 'string'}]}
        :return:
        """
        replaced_definitions_dict = def_dict
        def_names = def_dict.keys()
        for def_name in def_names:
            fields: Union[List[Dict], str] = def_dict[def_name]
            """
            fields: 
            [{'field': 'id', 'type': 'integer'}, '#/definitions/Category', {'field': 'name', 'type': 'string'}]
            """
            replace_target_dict = {}  # replace target input temporary
            for field_data in fields:
                if type(field_data) is str:
                    """
                    field_data:
                    '#/definitions/Category'
                    """
                    target_def_name: str = field_data[len(DEFINITIONS_HEADER):]
                    replace_target_fields = def_dict[field_data]
                    replaced_fields: List[Dict] = replace_definition(def_dict, target_def_name,
                                                                     replace_target_fields)
                    replace_target_dict[field_data] = replaced_fields
                """
                field_data:
                {'field': 'id', 'type': 'integer'}
                """
                # do nothing

            for k, v in replace_target_dict.items():
                """
                replace
                '#/definitions/Category' -> [{'field': 'id', 'type': 'integer'}, ...]
                example:
                {'#/definitions/Pet': [{'field': 'id', 'type': 'integer'}, '#/definitions/Category']
                -> {'#/definitions/Pet': [{'field': 'id', 'type': 'integer'}, '{'field': 'Category.id', 'type': 'integer'}]
                """
                replaced_definitions_dict[def_name].remove(k)
                replaced_definitions_dict[def_name].extend(v)
        return replaced_definitions_dict

    def create_definition_dict(definitions: Dict) -> Dict[str, List[Union[Dict[str, str], str]]]:
        def_dict: Dict = {}
        for def_key, def_values in definitions.items():
            """
            User:
              type: "object"
              properties:
            """
            props: Dict = def_values[PROPERTIES_KEY]
            fields: List[Dict] = []
            for prop_key, prop_values in props.items():
                if REF_KEY in prop_values.keys():
                    """
                    properties:
                      xxx:
                        $ref: "#/definitions/xxx"
                    """
                    fields.append(prop_values[REF_KEY])
                    continue
                if ITEMS_KEY in prop_values.keys():
                    """
                    properties:
                      xxx:
                        items:
                          $ref: "#/definitions/xxx"
                    """
                    prop_items = prop_values[ITEMS_KEY]
                    if REF_KEY in prop_items.keys():
                        fields.append(prop_items[REF_KEY])
                        continue
                    """
                    properties:
                      xxx:
                        items:
                          type: "string"
                    """
                    if TYPE_KEY in prop_items.keys():
                        fields.append({'field': prop_key, 'type': prop_items[TYPE_KEY]})
                        continue
                """
                properties:
                  id:
                    type: "integer"
                """
                fields.append({'field': prop_key, 'type': prop_values[TYPE_KEY]})
            def_dict[f'#/{DEFINITIONS_KEY}/{def_key}'] = fields
        return def_dict

    """
    definition_dict:
    {'#/definitions/Pet': [{'field': 'id', 'type': 'integer'}, '#/definitions/Category', {'field': 'name', 'type': 'string'}]}
    """
    definition_dict: Dict[str, List[Dict[str, str]]] = create_definition_dict(definitions_data)
    definition_dict = replace_definitions(definition_dict)
    return definition_dict


def paths_parser(paths: Dict) -> Dict[str, Union[List[Dict[str, str]], str]]:
    path_data_map = {}
    print('###  path list  ###')
    for path, methods in paths.items():
        if HTTP_METHOD_GET in methods.keys():
            print(path)
            responses: Dict = methods[HTTP_METHOD_GET][RESPONSES_KEY]
            if not STATUS_200_KEY in responses.keys():
                path_data_map[path] = []
                continue
            status_200_detail: Dict = responses[STATUS_200_KEY]
            if not SCHEMA_KEY in status_200_detail.keys():
                path_data_map[path] = []
                continue
            schema: Dict = methods[HTTP_METHOD_GET][RESPONSES_KEY][STATUS_200_KEY][SCHEMA_KEY]
            schema_keys = schema.keys()
            if len(schema_keys) == 1 and ITEMS_KEY in schema_keys:
                """
                [case]
                schema:
                    type: 
                """
                # path_data_map[path] = [{'field': '', 'value': '', 'type': schema[TYPE_KEY]}]
                path_data_map[path] = [{'field': '', 'type': schema[TYPE_KEY]}]
            if not REF_KEY in schema_keys and not ITEMS_KEY in schema_keys:
                """
                [case]
                schema:
                    xxxxxx:
                        type: 
                """
                # path_data_map[path] = [{'field': key, 'value': '', 'type': schema[key][TYPE_KEY]} for key in schema_keys
                #                       if key != TYPE_KEY]
                path_data_map[path] = [{'field': key, 'type': schema[key][TYPE_KEY]} for key in schema_keys if
                                       key != TYPE_KEY]
            if REF_KEY in schema_keys:
                """
                [case]
                schema:
                    $ref: "#/definitions/User"
                """
                path_data_map[path] = schema[REF_KEY]
            if ITEMS_KEY in schema_keys:
                """
                [case]
                schema:
                    type: "array"
                    items:
                """
                schema_items: Dict = schema[ITEMS_KEY]
                schema_items_keys = schema_items.keys()
                if REF_KEY in schema_items_keys:
                    """
                    [case]
                    items:
                        $ref: "#/definitions/User"
                    """
                    path_data_map[path] = schema_items[REF_KEY]
                if ENUM_KEY in schema_items_keys:
                    """
                    [case]
                    type: "string"
                    items:
                        enum:
                        - xxx
                    """
                    # path_data_map[path] = [{'field': '', 'value': schema_items[ENUM_KEY], 'type': 'string'}]
                    path_data_map[path] = [{'field': '', 'type': 'string'}]
    return path_data_map


def yaml_parser(yaml_data: Dict) -> Dict[str, List[Dict[str, str]]]:
    paths = yaml_data[PATHS_KEY]
    definitions = yaml_data[DEFINITIONS_KEY]
    def_dict: Dict[str, List[Dict[str, str]]] = definitions_parser(definitions)
    print('###  definitions  ###')
    print(def_dict)
    paths_dict: Dict[str, Union[List[Dict[str, str]], str]] = paths_parser(paths)
    print('###  paths (before replace definitions)  ###')
    print(paths_dict)
    # replace paths inner definition
    for path_key in paths_dict.keys():
        field_data = paths_dict[path_key]
        if type(field_data) is str:
            paths_dict[path_key] = def_dict[field_data]
    print('###  paths (after replace definitions)  ###')
    return paths_dict


def api_yaml_load() -> Dict[str, List[Dict[str, str]]]:
    with open("input/swagger_sample.yaml", mode="r") as f:
        yaml_data = yaml.safe_load(f)
    paths_dict = yaml_parser(yaml_data)
    print(paths_dict)
    return paths_dict


def main():
    api_yaml_load()


main()
