from typing import Dict, Union, List
from jinja2 import Template

import yaml

# yaml const value
HTTP_METHOD_GET = 'get'
PATHS_KEY = 'paths'
RESPONSES_KEY = 'responses'
STATUS_200_KEY = '200'
SCHEMA_KEY = 'schema'

SUMMARY_KEY = 'summary'
DESCRIPTION_KEY = 'description'
PRODUCES_KEY = 'produces'
PARAMETERS_KEY = 'parameters'

QUERY_NAME_KEY = 'name'
QUERY_IN_KEY = 'in'
QUERY_REQUIRED_KEY = 'required'
QUERY_DESCRIPTION_KEY = 'description'
QUERY_TYPE_KEY = 'type'

# API const value
BASE_URL = '/sym/v1/objects'

# Template
CONF_API_EXEC_BAT_TEMPLATE = '''
@ECHO OFF

SET HOST=127.0.0.1
SET PORT=8080
SET BASE_URL=/path/v1/objects
SET CONST_QUERY_NAME=
SET CONST_QUERY_VALUE=
'''

API_EXEC_BAT_TEMPLATE = '''
@ECHO OFF
SETLOCAL enabledelayedexpansion

call config.bat
SET API_PATH={{ path }}
SET QUERY=
ECHO API execute: {{ path }}
ECHO -----

IF NOT ""%CONST_QUERY_NAME%""=="""" (
  SET QUERY=^?%CONST_QUERY_NAME%^=%CONST_QUERY_VALUE%
)

SET URL=http://%HOST%:%PORT%%BASE_URL%%API_PATH%%QUERY%
ECHO %URL%
curl -v -H "Accept: {{ produces }}" -H "Content-Type: {{ produces }}" -x GET "%URL%"

ENDLOCAL
'''

EXIST_PARAM_API_EXEC_BAT_TEMPLATE = '''
@ECHO OFF
SETLOCAL enabledelayedexpansion

call config.bat
SET API_PATH={{ path }}
SET QUERY=
ECHO API execute: {{ path }}
ECHO -----
IF NOT ""%CONST_QUERY_NAME%""=="""" (
  SET QUERY=%CONST_QUERY_NAME%^=%CONST_QUERY_VALUE%
)
{% for paramObj in parameters %}
ECHO Param: {{ paramObj.param_name }} ({{ paramObj.param_type }})
ECHO   description {{ paramObj.description }}
:PARAM_INPUT
SET /P PARAM{{ loop.index }}="Input({{ paramObj.required }}):"
{% if paramObj.required == 'required' %}
IF ""%PARAM{{ loop.index }}%""=="""" GOTO PARAM_INPUT
{% endif %}

{% if paramObj.param_type == 'path' %}
SET PATH_NAME={% raw %}{{% endraw %}{{ paramObj.param_name }}{% raw %}}{% endraw %}
SET API_PATH=!API_PATH:%PATH_NAME%=%PARAM{{ loop.index }}%!
{% endif %}

{% if paramObj.param_type == 'query' %}
IF NOT "%CONST_QUERY_NAME%"=="{{ paramObj.param_name }}" (
{% if paramObj.required == 'optional' %}IF NOT ""%PARAM{{ loop.index }}%""=="""" ({% endif %}
IF ""!QUERY!""=="""" (
SET QUERY={{ paramObj.param_name }}^=%PARAM{{ loop.index }}%
) ELSE (
SET QUERY=^&!QUERY!{{ paramObj.param_name }}^=%PARAM{{ loop.index }}%
)
{% if paramObj.required == 'optional' %}){% endif %}
){% endif %}
{% endfor %}
IF NOT ""!QUERY!""=="""" (
  SET QUERY=^?!QUERY!
)

SET URL=http://%HOST%:%PORT%%BASE_URL%%API_PATH%%QUERY%
ECHO %URL%
curl -v -H "Accept: {{ produces }}" -H "Content-Type: {{ produces }}" -x GET "%URL%"

ENDLOCAL
'''


class ParamDetail:
    def __init__(self, param_info: Dict[str, str]):
        self.__param_name: str = param_info[QUERY_NAME_KEY]
        self.__param_type: str = param_info[QUERY_IN_KEY]
        self.__required: str = "required" if param_info[QUERY_REQUIRED_KEY] is True else "optional"
        self.__description: str = param_info[QUERY_DESCRIPTION_KEY]

    @property
    def param_name(self) -> str:
        return self.__param_name

    @property
    def param_type(self) -> str:
        return self.__param_type

    @property
    def required(self) -> str:
        return self.__required

    @property
    def description(self) -> str:
        return self.__description

    def convert_dict(self) -> Dict:
        return {
            "param_name": self.param_name,
            "param_type": self.param_type,
            "required": self.required,
            "description": self.description
        }


class ApiDetail:
    def __init__(self, path: str, api_detail: Dict):
        self.__path: str = path
        self.__summary: str = api_detail[SUMMARY_KEY]
        self.__description: str = api_detail[DESCRIPTION_KEY]
        self.__produces: str = api_detail[PRODUCES_KEY][0]
        self.__parameters: List[ParamDetail] = []
        for param_info in api_detail[PARAMETERS_KEY]:
            self.__parameters.append(ParamDetail(param_info))

    @property
    def path(self) -> str:
        return self.__path

    @property
    def summary(self) -> str:
        return self.__summary

    @property
    def description(self) -> str:
        return self.__description

    @property
    def produces(self) -> str:
        return self.__produces

    @property
    def parameters(self) -> List[ParamDetail]:
        return self.__parameters

    def convert_dict(self) -> dict:
        return {
            "path": self.path,
            "summary": self.summary,
            "description": self.description,
            "produces": self.produces,
            "parameters": [param.convert_dict() for param in self.parameters]
        }


def output_api_bat(api_detail: ApiDetail):
    is_path_var = '{' in api_detail.path and '}' in api_detail.path
    filename = api_detail.path[1:].replace('/', '_').replace('{', '').replace('}', '')
    if not is_path_var:
        template = Template(API_EXEC_BAT_TEMPLATE)
        exist_param_api_bat = template.render(api_detail.convert_dict())
        with open(f'./output/{filename}.bat', mode='w') as f:
            f.write(exist_param_api_bat)
    template = Template(EXIST_PARAM_API_EXEC_BAT_TEMPLATE)
    exist_param_api_bat = template.render(api_detail.convert_dict())
    with open(f'./output/{filename}_query.bat', mode='w') as f:
        f.write(exist_param_api_bat)
    with open('./output/config.bat', mode='w') as f:
        f.write(CONF_API_EXEC_BAT_TEMPLATE)


def yaml_paths_parser(paths: Dict) -> List[ApiDetail]:
    api_list = []
    print('###  path list  ###')
    for path_key, method_values in paths.items():
        if HTTP_METHOD_GET in method_values.keys():
            print(path_key)
            api_detail = method_values[HTTP_METHOD_GET]
            api_list.append(ApiDetail(path_key, api_detail))
    return api_list


def main():
    with open("input/swagger_sample.yaml", mode="r") as f:
        yaml_data = yaml.safe_load(f)
    paths = yaml_data[PATHS_KEY]
    api_details = yaml_paths_parser(paths)
    for api in api_details:
        output_api_bat(api)


main()
