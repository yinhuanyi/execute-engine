# coding: utf-8
"""
@Author: Robby
@Module name: zabbix_send_data.py
@Create date: 2020-11-20
@Function: 
"""

import json
import struct
import socket
import time
import re

from utils.global_logger import getlogger
from utils.const_file import ZABBIX_INFO_LOG, ZABBIX_ERROR_LOG


zabbix_logger = getlogger(logger_name='heartBeat', info_file_path=ZABBIX_INFO_LOG, error_file_path=ZABBIX_ERROR_LOG)



class ZabbixSender:

    def __init__(self, server, port, host, key, value):
        self.package = {'request': 'sender data', 'data': [{'host': str(host), 'key': str(key), 'value': str(value)}]}
        self.server = server
        self.port = port

    def send(self):
        data_length = struct.pack('<Q', len(json.dumps(self.package)))
        packet = str(json.dumps(self.package)).encode('utf-8')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            s.connect((self.server, int(self.port)))
            s.settimeout(2)
        except Exception as e:
            zabbix_logger.error('Connect to Zabbix Server TCP Error, Message: {}'.format(e))
            s.close()
            return

        try:
            s.sendall('ZBXD\1'.encode('utf-8'))
            s.sendall(data_length)
            s.sendall(packet)
            time.sleep(1)
            status = s.recv(1024).decode('utf-8')
            '''
            ZBXDZ......{"response":"success","info":"processed: 2; failed: 0; total: 2; seconds spent: 0.000039"}
            ZBXDZ......{"response":"success","info":"processed: 0; failed: 2; total: 2; seconds spent: 0.000032"}
            '''

            re_status = re.compile('(\{.*\})')
            status = re_status.search(status).groups()[0]
            return status

        except Exception as e:
            zabbix_logger.error('Send Data to Zabbix Server Error, Message: {}'.format(e))

        finally:
            s.close()


if __name__ == '__main__':
    # 这里的IP是proxy的IP，不是server的IP
    zabbix_sender = ZabbixSender('10.102.0.13', 10051, 'yw1-2', 'exec.engine.ping', '1')
    ret = zabbix_sender.send()
    print(ret)