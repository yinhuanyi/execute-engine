# coding: utf-8
"""
@Author: Robby
@Module name: const_file.py
@Create date: 2020-09-09
@Function: 全局常量
"""

import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(PROJECT_DIR, 'logs')
CONF_DIR = os.path.join(PROJECT_DIR, 'conf')
DATA_DIR = os.path.join(PROJECT_DIR, 'data')

# PID文件
PID_FILE = os.path.join(PROJECT_DIR, 'engine.pid')

# 配置文件
SERVER_CONFIG = os.path.join(CONF_DIR, 'server.conf')
PLAYBOOK_DIR = os.path.join(DATA_DIR, 'playbooks')

# 日志文件
ENGILE_LOG = os.path.join(LOG_DIR, 'engine.log')
ADHOC_INFO_LOG = os.path.join(LOG_DIR, 'adhoc_info.log')
ADHOC_ERROR_LOG = os.path.join(LOG_DIR, 'adhoc_error.log')
PLAYBOOK_INFO_LOG = os.path.join(LOG_DIR, 'playbook_info.log')
PLAYBOOK_ERROR_LOG = os.path.join(LOG_DIR, 'playbook_error.log')
CONSUMER_INFO_LOG = os.path.join(LOG_DIR, 'consumer_info.log')
CONSUMER_ERROR_LOG = os.path.join(LOG_DIR, 'consumer_error.log')
SQL_INFO_LOG = os.path.join(LOG_DIR, 'sql_info.log')
SQL_ERROR_LOG = os.path.join(LOG_DIR, 'sql_error.log')
ZABBIX_INFO_LOG = os.path.join(LOG_DIR, 'zabbix_info.log')
ZABBIX_ERROR_LOG = os.path.join(LOG_DIR, 'zabbix_error.log')
SUBPROCESS_LOG = os.path.join(LOG_DIR, 'subprocess.log')

# 测试的指令集json内容
COMMAND_JSON = os.path.join(DATA_DIR, 'ansible_adhoc.json')

if __name__ == '__main__':
    print(PROJECT_DIR)
    print(LOG_DIR)
    print(CONF_DIR)
    print(SERVER_CONFIG)
    print(PLAYBOOK_FILE)
    print(ADHOC_INFO_LOG)
    print(ADHOC_ERROR_LOG)
    print(PLAYBOOK_INFO_LOG)
    print(PLAYBOOK_ERROR_LOG)
    print(COMMAND_JSON)
    print(CONSUMER_INFO_LOG)
    print(SQL_INFO_LOG)
    print(SQL_ERROR_LOG)