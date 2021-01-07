# coding: utf-8
"""
@Author: Robby
@Module name:
@Create date: 2020-11-17
@Function: xb-cl01-se-063-001 做测试
"""
import sys
import os
import signal
from daemonization import Daemonize

from utils.const_file import PID_FILE, ENGILE_LOG
from utils.global_logger import getlogger
from tasks import start_engine

# 让守护进程正确日志和错误日志输出到同一个文件中

engile_logger = getlogger(logger_name='engine', info_file_path=ENGILE_LOG, error_file_path=ENGILE_LOG)

if len(sys.argv) != 2:
    print('Usage:python {} [start|stop]'.format(sys.argv[0]), file=sys.stderr)
    raise SystemExit(1)

if sys.argv[1] == 'start':
    try:
        daemon = Daemonize(pidfile=PID_FILE, stdout=ENGILE_LOG, stderr=ENGILE_LOG)
        daemon.start()
        print('Engine Start Success', file=sys.stdout)
        engile_logger.info('Engine Start Success')
    except RuntimeError as e:
        engile_logger.error('Engine Start Error, Message: {}'.format(e))
        raise SystemExit(1)

    start_engine()

elif sys.argv[1] == 'stop':
    if os.path.exists(PID_FILE):
        try:
            # 获取全局Event事件，设置为True，让线程退出 0x7fa899b52e80
            with open(PID_FILE) as f:
                os.kill(int(f.read()), signal.SIGKILL)
                os.remove(PID_FILE)
                print('Engine Stop Success', file=sys.stdout)
                engile_logger.info('Engine Stop Success')
        except Exception as e:
            with open(PID_FILE) as f:
                os.kill(int(f.read()), signal.SIGTERM)
            engile_logger.error('Engine Stop Fail, Message: {}'.format(e))
    else:
        print('Engine Not Running', file=sys.stderr)
        raise SystemExit(1)

else:
    print('Unknown command {}'.format(sys.argv[1]), file=sys.stderr)
    raise SystemExit(1)