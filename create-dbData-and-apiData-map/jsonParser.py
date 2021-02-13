import json
from typing import Dict, List, Union

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
        self.data_list: List[BaseDataList.BaseData] = []

    def add(self, table: str, field: str):
        self.data_list.append(BaseDataList.BaseData(table, field))

    def getTableName(self, field_name) -> Union[str, None]:
        for data in self.data_list:
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
        self.data_list: List[DbDataList.DbData] = []

    def add(self, table: str, field: str, column: str):
        self.data_list.append(DbDataList.DbData(table, field, column))

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

    def __init__(self):
        self.data_list: List[MappingSqlFieldList.MappingSqlField] = []

    def add(self, mapping_list: List[Dict[str, List[str]]]):
        for mapping_dict in mapping_list:
            for db_field_name in mapping_dict.keys():
                self.data_list.append(MappingSqlFieldList.MappingSqlField(db_field_name, mapping_dict[db_field_name]))

    def getBaseFields(self, db_field_name) -> Union[List[str], None]:
        for data in self.data_list:
            if data.db_field == db_field_name:
                return data.base_fields
        return None


class MappingTableAndFieldList:
    class MappingTableAndField:
        # convert from BaseDataList and DbDataList and MappingSqlFieldList
        def __init__(self, db_table: str, db_field: str, base_name: str, base_field: str):
            self.db_table = db_table
            self.db_field = db_field
            self.base_name = base_name
            self.base_field = base_field

    def __init__(self, db_data_list: DbDataList, base_data_list: BaseDataList, mapping_list: MappingSqlFieldList):
        self.data_list: List[MappingTableAndFieldList.MappingTableAndField] = self.convert(db_data_list, base_data_list,
                                                                                           mapping_list)

    @staticmethod
    def convert(db_data_list: DbDataList, base_data_list: BaseDataList, mapping_list: MappingSqlFieldList) -> List:
        data_list: List[MappingTableAndFieldList.MappingTableAndField] = []
        for db_data in db_data_list.data_list:
            base_fields = mapping_list.getBaseFields(db_data.field)
            if base_fields is None:
                continue
            for base_field in base_fields:
                table_name = base_data_list.getTableName(base_field)
                if table_name is None:
                    continue
                data_list.append(
                    MappingTableAndFieldList.MappingTableAndField(db_data.table, db_data.field, table_name, base_field))
        return data_list


class MappingBaseAndApi:
    def __init__(self):
        self.base_name = ''
        self.api_name = ''
        self.field = ''


class MappingDbAndApiData:
    def __init__(self):
        self.db_table_name = ''
        self.db_field = ''
        self.api_name = ''
        self.api_res_filed = ''


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
    MappingTableAndFieldList(db_data_list, base_data_list, mapping_sql_list)
    # mapping api and db data


def main():
    with open("input/definition.json", mode="r") as f:
        json_data = json.load(f)
    json_parser(json_data)


main()
