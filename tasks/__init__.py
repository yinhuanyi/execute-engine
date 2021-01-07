# coding: utf-8
"""
@Author: Robby
@Module name: __init__.py.py
@Create date: 2020-12-21
@Function: 
"""

from multiprocessing import Process

from utils.const_file import  ENGILE_LOG
from utils.global_logger import getlogger
from utils.parse_file import EventSingleton
from .process_task.consume_message import consume_kafka_message
from .process_task.zabbix_heart_beat import send_zabbix_heart_beat

engine_logger = getlogger(logger_name='engine', info_file_path=ENGILE_LOG, error_file_path=ENGILE_LOG)

def start_engine():
    global_event = EventSingleton.getEventInstance()

    Process(target=consume_kafka_message, args=(global_event, ), name='consume_kafka_message').start()
    Process(target=send_zabbix_heart_beat, args=(global_event, ), name='send_zabbix_heart_beat').start()


if __name__ == '__main__':
    start_engine()