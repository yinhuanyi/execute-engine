# coding: utf-8
"""
@Author: Robby
@Module name:
@Create date: 2020-11-17
@Function: 
"""

import os
import sys


from utils.global_logger import getlogger
from utils.const_file import LOG_DIR
from utils.const_file import PID_FILE



class Daemonize:
    def __init__(self, pidfile=PID_FILE, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.pidfile = pidfile
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.log_dir = LOG_DIR
        self.logger = getlogger(logger_name='daemon',
                                info_file_path=self.stdout,
                                error_file_path=self.stderr,)

    def start(self):
        if os.path.exists(self.pidfile):
            raise RuntimeError('Agent Is Already Running')

        self.__fork_process()

    def __fork_process(self):
        try:
            if os.fork() > 0:
                raise SystemExit(0)
        except OSError as e:
            self.logger.error('Fork Subprocess Error， Message: {}'.format(e))
            self.logger.error('Fork Subprocess Error')
            raise RuntimeError('Fork Subprocess Error')


        self.__dispatch_terminal()

    def __dispatch_terminal(self):
        os.chdir('/')
        os.umask(0)
        os.setsid()

        self.__fork_process_again()

    def __fork_process_again(self):
        try:
            if os.fork() > 0:
                raise SystemExit(0)
        except OSError as e:
            self.logger.error('Fork Subprocess Again Error， Message: {}'.format(e))
            raise RuntimeError('Fork Subprocess Error')

        self.__flush_standout()

    def __flush_standout(self):
        sys.stdout.flush()
        sys.stderr.flush()
        self.__alterminate_parents_fileno()

    # 将制定日志文件的描述符复制一份到标准输入、输出、错误输出
    def __alterminate_parents_fileno(self):
        with open(self.stdin, 'rb', 0) as f:
            os.dup2(f.fileno(), sys.stdin.fileno())

        with open(self.stdout, 'ab', 0) as f:
            os.dup2(f.fileno(), sys.stdin.fileno())

        with open(self.stderr, 'ab', 0) as f:
            os.dup2(f.fileno(), sys.stderr.fileno())

        self.__write_pidfile()

    def __write_pidfile(self):
        try:
            with open(self.pidfile, 'w+') as f:
                print(os.getpid(), file=f)

        except Exception as e:
            self.logger.error('Write Pid File Error, Message: {}'.format(e))