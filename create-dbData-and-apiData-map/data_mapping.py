import json
from typing import Dict, List, Union, Optional

from jinja2 import FileSystemLoader, Environment

from apiYamlParser import api_yaml_load
from parser_utils import get_target_from_json
from sqlparser import sql_parser

BASE_DATA_PATH = ['base']
BASE_DATA_NAME_KEY = "name"
BASE_DATA_FIELD_KEY = ['field']
SQL_PATH = ['sql']
DB_TABLE_PAH = ['db_def']
DB_TABLE_KEY = 'table'
DB_FIELD_TYPE_KEYS = ['db_fields']
DB_FILED_NAME_KEYS = ['field']
DB_FILED_COLUMN_KEY = 'column'


# json data
class BaseDataList:
    class BaseData:
        def __init__(self, table: str, field: str):
            self.__table = table
            self.__field = field

        @property
        def table(self):
            return self.__table

        @property
        def field(self):
            return self.__field

    def __init__(self):
        self.__data_list: List[BaseDataList.BaseData] = []

    def add(self, table: str, field: str):
        self.__data_list.append(BaseDataList.BaseData(table, field))

    def getTableName(self, field_name) -> Union[str, None]:
        for data in self.__data_list:
            if data.field == field_name:
                return data.table
        return None


class DbDataList:
    class DbData:
        def __init__(self, table: str, field: str, column: str):
            self.__table = table
            self.__field = field
            self.__base_sql_column = column  # equal base_field

        @property
        def table(self):
            return self.__table

        @property
        def field(self):
            return self.__field

        @property
        def base_sql_column(self):
            return self.__base_sql_column

    def __init__(self):
        self.__data_list: List[DbDataList.DbData] = []

    @property
    def data_list(self):
        return self.__data_list

    def add(self, table: str, field: str, column: str):
        self.__data_list.append(DbDataList.DbData(table, field, column))

    # def getTableName(self, field_name) -> Union[str, None]:
    #     for data in self.data_list:
    #         if data.field == field_name:
    #             return data.table
    #     return None


# convert data
class MappingSqlFieldList:
    class MappingSqlField:
        # result of sql parser
        def __init__(self, db_field_name: str, base_field_names: List[str]):
            self.__db_field = db_field_name
            self.__base_fields = base_field_names

        @property
        def db_field(self):
            return self.__db_field

        @property
        def base_fields(self):
            return self.__base_fields

    def __init__(self, mapping_list: List[Dict[str, List[str]]]):
        self.__data_list: List[MappingSqlFieldList.MappingSqlField] = self.convert(mapping_list)

    @staticmethod
    def convert(mapping_list: List[Dict[str, List[str]]]) -> List[MappingSqlField]:
        data_list = []
        for mapping_dict in mapping_list:
            for db_field_name in mapping_dict.keys():
                data_list.append(MappingSqlFieldList.MappingSqlField(db_field_name, mapping_dict[db_field_name]))
        return data_list

    def getBaseFields(self, db_field_name) -> Union[List[str], None]:
        for data in self.__data_list:
            if data.db_field == db_field_name:
                return data.base_fields
        return None


class MappingDbAndBaseDataList:
    # convert from BaseDataList and DbDataList and MappingSqlFieldList
    class MappingDbAndBaseData:
        def __init__(self, db_table: str, db_field: str, base_name: str, base_field: str):
            self.__db_table = db_table
            self.__db_field = db_field
            self.__base_name = base_name
            self.__base_field = base_field

        @property
        def db_table(self):
            return self.__db_table

        @property
        def db_field(self):
            return self.__db_field

        @property
        def base_name(self):
            return self.__base_name

        @property
        def base_field(self):
            return self.__base_field

    def __init__(self, db_data_list: DbDataList, base_data_list: BaseDataList, mapping_list: MappingSqlFieldList):
        self.__data_list: List[MappingDbAndBaseDataList.MappingDbAndBaseData] \
            = self.convert(db_data_list, base_data_list, mapping_list)

    @property
    def data_list(self):
        return self.__data_list

    @staticmethod
    def convert(db_data_list: DbDataList, base_data_list: BaseDataList, mapping_list: MappingSqlFieldList) -> List:
        data_list: List[MappingDbAndBaseDataList.MappingDbAndBaseData] = []
        for db_data in db_data_list.data_list:
            base_fields = mapping_list.getBaseFields(db_data.field)
            if base_fields is None:
                continue
            for base_field in base_fields:
                table_name = base_data_list.getTableName(base_field)
                if table_name is None:
                    continue
                data_list.append(
                    MappingDbAndBaseDataList.MappingDbAndBaseData(db_data.table, db_data.field, table_name, base_field))
        return data_list


# from mapping_conf.json
class MappingBaseAndApiDataList:
    class MappingBaseAndApiData:
        def __init__(self, base_name: str, api_name: str):
            self.__base_name = base_name
            self.__api_name = api_name

        @property
        def base_name(self):
            return self.__base_name

        @property
        def api_name(self):
            return self.__api_name

    def __init__(self, api_base_name_map: Dict[str, str]):
        self.__data_list = self.convert(api_base_name_map)

    @staticmethod
    def convert(api_base_name_dict: Dict[str, str]) -> List[MappingBaseAndApiData]:
        data_list = []
        for base_name, api_name in api_base_name_dict:
            data_list.append(MappingBaseAndApiDataList.MappingBaseAndApiData(base_name, api_name))
        return data_list

    def getApiName(self, base_name) -> Union[str, None]:
        for data in self.__data_list:
            if data.base_name == base_name:
                return data.api_name
        return None


class ApiFieldDataList:
    class ApiFieldData:
        FIELD_KEY = 'field'
        TYPE_KEY = 'type'
        MAXIMUM_KEY = 'maximum'
        MINIMUM_KEY = 'minimum'
        MAX_LEN_KEY = 'maxlength'
        MIN_LEN_KEY = 'minlength'

        def __init__(self, api_path: str, field_data_dict: Dict[str, str]):
            self.__api_name: str = api_path
            self.__field_name: str = field_data_dict[self.FIELD_KEY]
            self.__field_type: str = field_data_dict[self.TYPE_KEY] if self.TYPE_KEY in field_data_dict else ''
            self.__field_max_val: str = field_data_dict[self.MAXIMUM_KEY] if self.MAXIMUM_KEY in field_data_dict else ''
            self.__field_min_val: str = field_data_dict[self.MINIMUM_KEY] if self.MINIMUM_KEY in field_data_dict else ''
            self.__field_max_len: str = field_data_dict[self.MAX_LEN_KEY] if self.MAX_LEN_KEY in field_data_dict else ''
            self.__field_min_len: str = field_data_dict[self.MIN_LEN_KEY] if self.MIN_LEN_KEY in field_data_dict else ''

        @property
        def api_name(self):
            return self.__api_name

        @property
        def field_name(self):
            return self.__field_name

        @property
        def field_type(self):
            return self.__field_type

        @property
        def field_max_val(self):
            return self.__field_max_val

        @property
        def field_min_val(self):
            return self.__field_min_val

        @property
        def field_max_len(self):
            return self.__field_max_len

        @property
        def field_min_len(self):
            return self.__field_min_len

    def __init__(self, api_data_list: Dict[str, List[Dict[str, str]]]):
        self.__data_list = self.convert(api_data_list)

    @staticmethod
    def convert(api_data_dict: Dict[str, List[Dict[str, str]]]) -> List[ApiFieldData]:
        data_list = []
        for api_data_path, api_field_data_list in api_data_dict.items():
            for field_data_dict in api_field_data_list:
                if ApiFieldDataList.ApiFieldData.FIELD_KEY in field_data_dict:
                    data_list.append(ApiFieldDataList.ApiFieldData(api_data_path, field_data_dict))
        return data_list

    def getApiFieldData(self, api_name, field_name) -> Optional[ApiFieldData]:
        for api_data in self.__data_list:
            if api_data.api_name == api_name and api_data.field_name == field_name:
                return api_data
        return None


# final result
class MappingDbAndApiDataList:
    class MappingDbAndApiData:
        def __init__(self, db_base_data: MappingDbAndBaseDataList.MappingDbAndBaseData,
                     api_data: ApiFieldDataList.ApiFieldData):
            self.__db_table = db_base_data.db_table  # from MappingDbAndBaseDataList and MappingBaseAndApiDataList
            self.__db_field = db_base_data.db_field  # from MappingDbAndBaseDataList
            self.__base_name = db_base_data.base_name  # from MappingDbAndBaseDataList
            self.__base_field = db_base_data.base_field  # from MappingDbAndBaseDataList
            self.__api_name = api_data.api_name  # from ApiFieldDataList and MappingBaseAndApiDataList
            self.__api_field_name = api_data.field_name  # from ApiFieldDataList
            self.__api_field_type = api_data.field_type  # from ApiFieldDataList
            self.__api_field_max_val = api_data.field_max_val  # from ApiFieldDataList
            self.__api_field_min_val = api_data.field_min_val  # from ApiFieldDataList
            self.__api_field_max_len = api_data.field_max_len  # from ApiFieldDataList
            self.__api_field_min_len = api_data.field_min_len  # from ApiFieldDataList

        @property
        def db_table(self):
            return self.__db_table

        @property
        def db_field(self):
            return self.__db_field

        @property
        def base_name(self):
            return self.__base_name

        @property
        def base_field(self):
            return self.__base_field

        @property
        def api_name(self):
            return self.__api_name

        @property
        def api_field_name(self):
            return self.__api_field_name

        @property
        def api_field_type(self):
            return self.__api_field_type

        @property
        def api_field_max_val(self):
            return self.__api_field_max_val

        @property
        def api_field_min_val(self):
            return self.__api_field_min_val

        @property
        def api_field_max_len(self):
            return self.__api_field_max_len

        @property
        def api_field_min_len(self):
            return self.__api_field_min_len

    def __init__(self, db_base_mappings: MappingDbAndBaseDataList, base_api_mappings: MappingBaseAndApiDataList,
                 api_data: ApiFieldDataList):
        self.data_list = self.convert(db_base_mappings, base_api_mappings, api_data)

    @staticmethod
    def convert(db_base_mappings: MappingDbAndBaseDataList, base_api_mappings: MappingBaseAndApiDataList,
                api_data_list: ApiFieldDataList):
        data_list = []
        for db_base_data in db_base_mappings.data_list:
            api_name: str = base_api_mappings.getApiName(db_base_data.base_name)
            field_name: str = db_base_data.base_field
            api_field_data: ApiFieldDataList.ApiFieldData = api_data_list.getApiFieldData(api_name, field_name)
            data_list.append(MappingDbAndApiDataList.MappingDbAndApiData(db_base_data, api_field_data))
        return data_list

    def convert_json(self) -> List[Dict[str, str]]:
        converted_list = []
        for data in self.data_list:
            converted_list.append({
                'db_table': data.db_table,
                'db_field': data.db_field,
                'base_name': data.base_name,
                'base_field': data.base_field,
                'api_name': data.api_name,
                'api_field_name': data.api_field_name,
                'api_field_type': data.api_field_type,
                'api_field_max_val': data.api_field_max_val,
                'api_field_min_val': data.api_field_min_val,
                'api_field_max_len': data.api_field_max_len,
                'api_field_min_len': data.api_field_min_len
            })
        return converted_list


def db_data_part_json_parser(json_data: Dict) -> DbDataList:
    # db def
    db_data_list = DbDataList()
    json_db_data = get_target_from_json(json_data, DB_TABLE_PAH)
    table_name = json_db_data[DB_TABLE_KEY]
    for field_type_key in DB_FIELD_TYPE_KEYS:
        filed_data_list: List[Dict] = json_db_data[field_type_key]
        for field_data in filed_data_list:
            for key in DB_FILED_NAME_KEYS:
                if not key in field_data:
                    continue
                db_data_list.add(table_name, field_data[key], field_data[DB_FILED_COLUMN_KEY])
    return db_data_list


def base_data_part_json_parser(json_data: Dict) -> BaseDataList:
    base_data_list = BaseDataList()
    json_base_data: List[Dict] = get_target_from_json(json_data, BASE_DATA_PATH)
    for data_dict in json_base_data:
        for field_key in BASE_DATA_FIELD_KEY:
            fields: List[str] = data_dict[field_key]
            for field in fields:
                base_data_list.add(data_dict[BASE_DATA_NAME_KEY], field)
    return base_data_list


def json_parser(json_data: Dict):
    # base data parse
    base_data_list: BaseDataList = base_data_part_json_parser(json_data)
    # db data parse
    db_data_list: DbDataList = db_data_part_json_parser(json_data)
    # sql parse
    result: List[Dict[str, List[str]]] = sql_parser(json_data, SQL_PATH)
    mapping_sql_list = MappingSqlFieldList(result)
    # mapping db data and base data
    mapping_db_base_list = MappingDbAndBaseDataList(db_data_list, base_data_list, mapping_sql_list)
    # get mapping api and base data
    with open("input/mapping_conf.json", mode="r") as f:
        mapping_json_data: Dict[str, str] = json.load(f)
    mapping_base_api_list = MappingBaseAndApiDataList(mapping_json_data)
    # api yml parse
    api_data_list: Dict[str, List[Dict[str, str]]] = api_yaml_load()
    api_field_list = ApiFieldDataList(api_data_list)
    # mapping db data nad base data and api data
    mapping_data_list = MappingDbAndApiDataList(mapping_db_base_list, mapping_base_api_list, api_field_list)
    # output file
    env = Environment(loader=FileSystemLoader('./template'))
    template = env.get_template('mapping_result.md')
    data = {'mapping_result_list': mapping_data_list.convert_json()}
    md_file_data = template.render(data)
    with open('./output/specification.md', mode='w') as f:
        f.write(md_file_data)


def main():
    with open("input/definition.json", mode="r") as f:
        def_json_data = json.load(f)
    json_parser(def_json_data)


main()
