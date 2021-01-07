# coding: utf-8
"""
@Author: Robby
@Module name: data_test.py
@Create date: 2020-10-28
@Function: 读取本地文件内容，发送到kafka
"""

import json
from utils.const_file import COMMAND_JSON

def get_cmd_dict_data():
    with open(COMMAND_JSON) as file:
        dict_data = json.load(file)
    return dict_data