# coding: utf-8
"""
@Author: Robby
@Module name:
@Create date: 2020-11-17
@Function: 
"""

from multiprocessing import Event
import multiprocessing

from utils.const_file import ZABBIX_INFO_LOG, ZABBIX_ERROR_LOG, SUBPROCESS_LOG
from utils.global_logger import getlogger
from utils.parse_file import  ProcessExecInterval, ZabbixServerConfigSingleton
from utils.zabbix_send_data import ZabbixSender
from utils import get_hostname


zabbix_logger = getlogger(logger_name='zabbix', info_file_path=ZABBIX_INFO_LOG, error_file_path=ZABBIX_ERROR_LOG)
subprocess_logger = getlogger(logger_name='subprocess', info_file_path=SUBPROCESS_LOG, error_file_path=SUBPROCESS_LOG)

def send_zabbix_heart_beat(event: Event):
    interval = ProcessExecInterval._get_zabbix_interval()
    zabbix_server_ip, port, item = ZabbixServerConfigSingleton._get_zabbix_server_config_info()

    while not event.wait(int(interval)):
        hostname = get_hostname()
        subprocess_logger.info('Current Process is : {}'.format(multiprocessing.current_process().name))

        try:
            zabbix_logger.info(zabbix_server_ip, int(port), hostname, item, '1')
            zabbix_sender = ZabbixSender(zabbix_server_ip, int(port), hostname, item, '1')
            ret = zabbix_sender.send()
            zabbix_logger.info(ret)

        except Exception as e:
            zabbix_logger.error('Zabbix Send Package Error: {}'.format(e))
            event.set()

if __name__ == '__main__':
    send_zabbix_heart_beat(Event())