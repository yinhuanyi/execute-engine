# coding: utf-8
"""
@Author: Robby
@Module name: cmd_api.py
@Create date: 2020-11-04
@Function: 封装adhoc接口
"""

import shutil
import time
from func_timeout import func_timeout, FunctionTimedOut

# 导入ansible的核心类
import ansible.constants as C
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.module_utils.common.collections import ImmutableDict
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.vars.manager import VariableManager
from ansible import context
from execute_api.custom_callback.adhoc_callback import AdHocCallback
from utils.const_file import ADHOC_INFO_LOG, ADHOC_ERROR_LOG, SQL_ERROR_LOG, SQL_INFO_LOG
from utils.global_logger import getlogger
from execute_api.custom_callback_serialization.adhoc_serialization import adhoc_callback_to_mysql
from utils.parse_file import FlagSingleton
from utils.parse_file import MySQLSessionSingleton, AnsibleConfigSingleton
from model import adhoc


adhoc_logger = getlogger('adhoc', ADHOC_INFO_LOG, ADHOC_ERROR_LOG)
sql_logger = getlogger('sql', SQL_INFO_LOG, SQL_ERROR_LOG)

ssh_user, ssh_password, ssh_sudo_password =  AnsibleConfigSingleton._get_ansible_config_info()


# 单一任务执行器
class AdHocSingleTask:
    __loader = None
    __callback = None
    __inventory = None
    __variable_manager = None

    def __init__(self, host: str, module: str, args: str, exec_timeout=60, ssh_user=ssh_user, ssh_password=ssh_password, ssh_sudo_password=ssh_sudo_password, python_interpreter='/usr/bin/python3',):
        self.host = host
        self.module = module
        self.args = args
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.ssh_sudo_password = ssh_sudo_password
        self.python_interpreter = python_interpreter
        self.exec_timeout = exec_timeout

    def __get_sources(self):
        host_list = self.host.replace(' ', '').strip(',').split(',')
        sources = ','.join(host_list)
        if len(host_list) == 1:
            sources += ','

        # 这是ansible.cfg参数
        context.CLIARGS = ImmutableDict(connection='smart',
                                        module_path=None,
                                        timeout=3,
                                        forks=10,
                                        become=True,
                                        become_method='sudo',
                                        become_user='root',
                                        check=False,
                                        become_ask_pass=False,
                                        command_warnings=False,
                                        deprecation_warnings=False,
                                        system_warnings=False,
                                        diff=False,
                                        verbosity=5,
                                        host_key_checking=False,
                                        gathering=False,
                                        )


        return sources

    def __get_loader(self):
        if self.__loader == None:
            self.__loader = DataLoader()
        return self.__loader

    def __get_callback(self):
        if self.__callback == None:
            self.__callback = AdHocCallback()
        return self.__callback

    def __get_inventory(self):
        if self.__inventory == None:
            self.__inventory = InventoryManager(loader=self.__get_loader(), sources=self.__get_sources())
        return self.__inventory

    def __get_variable_manager(self):
        if self.__variable_manager == None:
            host_list = self.host.replace(' ', '').strip(',').split(',')
            variable_manager = VariableManager(loader=self.__get_loader(), inventory=self.__get_inventory())

            for host in host_list:
                variable_manager.set_host_variable(host=host, varname='ansible_ssh_user', value=self.ssh_user)
                variable_manager.set_host_variable(host=host, varname='ansible_ssh_pass', value=self.ssh_password)
                variable_manager.set_host_variable(host=host, varname='ansible_sudo_pass', value=self.ssh_sudo_password)
                variable_manager.set_host_variable(host=host, varname='ansible_python_interpreter', value=self.python_interpreter)
                variable_manager.set_host_variable(host=host, varname='strategy', value='free')

            self.__variable_manager = variable_manager

        return self.__variable_manager

    def __get_task_queue_manager(self):
        return TaskQueueManager(
                inventory=self.__get_inventory(),
                variable_manager=self.__get_variable_manager(),
                loader=self.__get_loader(),
                passwords=dict(vault_pass='secret'),
                stdout_callback=self.__get_callback(),)

    def __get_play_source(self):
        return dict(
                    name="Ansible Play",
                    hosts=self.host.replace(' ', '').strip(',').split(','),
                    gather_facts='no',
                    tasks=[dict(action={'module': self.module, 'args': self.args}),])

    def exec_adhoc_task(self):
        play = Play().load(self.__get_play_source(), variable_manager=self.__get_variable_manager(), loader=self.__get_loader())
        tqm = self.__get_task_queue_manager()
        try:
            func_timeout(int(self.exec_timeout), tqm.run, args=(play, ))

        except FunctionTimedOut as e:
            adhoc_logger.error('AdHoc TIMEOUT Error: hosts={} module={} args={}'.format(self.host, self.module, self.args))
            # 将超时信息写入到数据表
            session = MySQLSessionSingleton._get_mysql_session()
            try:
                for host in self.host.replace(' ', '').strip(',').split(','):

                    asset_instance = session.query(adhoc.Asset).filter(adhoc.Asset.ip == host).order_by(adhoc.Asset.id.desc()).first()
                    asset_instance.result_table = adhoc.ExecTimeout.__tablename__
                    exec_timeout_instance = adhoc.ExecTimeout(asset_id=asset_instance.id,
                                                              module=self.module,
                                                              args=self.args,
                                                              msg='Exec Timeout')
                    session.add(exec_timeout_instance)
                    session.commit()

            except Exception as e:
                sql_logger.error('SQL Error: '.format(e))
                session.rollback()

            finally:
                session.close()


        except Exception as e:
            adhoc_logger.error('AdHoc EXEC Error: {}'.format(e))

        finally:
            tqm.cleanup()
            loader = self.__get_loader()
            if loader:
                loader.cleanup_all_tmp_files()
            # 移除ansible tmp 目录
            shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)
            time.sleep(1)
            FlagSingleton._set_flag(True)

        # 数据入库
        adhoc_callback_to_mysql(self, self.__get_callback())


if __name__ == '__main__':
    # single_adhoc_task('10.110.119.5', 'shell', 'apt install -y apache2')
    # single_adhoc_task('10.110.119.5', 'shell', 'apt remove -y apache2')
    # single_adhoc_task('10.110.119.5', 'shell', 'systemctl stop apache2')
    # single_adhoc_task('10.110.119.5', 'shell', 'systemctl enable apache2')
    # single_adhoc_task('10.110.175.6', 'shell', 'touch /tmp/test.txt')
    # single_adhoc_task('10.110.175.6', 'shell', 'ls -l /tmp/test.txt')
    # single_adhoc_task('10.110.175.6', 'shell', 'rm -f /tmp/test.txt')
    # single_adhoc_task('10.110.175.6', 'shell', 'ls -l /tmp/test.txt')
    # single_adhoc_task('10.101.175.6', 'shell', 'ls -l /tmp/test.txt')
    # single_adhoc_task('10.110.119.5', 'copy', 'src=/etc/fstab1 dest=/tmp/fstab1')
    # single_adhoc_task('10.110.135.4', 'copy', 'src=/etc/fstab dest=/tmp/fstab')

    # task = AdHocSingleTask('10.110.167.1', 'shell', 'pip3 install sqlalchemy', exec_timeout=100)
    # task.exec_adhoc_task()

    # single_task = AdHocSingleTask('10.110.103.3,10.110.103.4,10.110.103.6,10.110.103.11,10.110.103.12,10.110.103.14,10.110.103.19,10.110.103.20,10.110.103.21,10.110.103.22,10.110.103.23,10.110.103.26,10.110.103.28,10.110.103.101,10.110.103.102,10.110.103.106,10.110.103.107,10.110.103.108,10.110.103.3,10.110.103.4,10.110.103.6,10.110.103.11,10.110.103.12,10.110.103.14,10.110.103.19,10.110.103.20,10.110.103.21,10.110.103.22,10.110.103.23,10.110.103.26,10.110.103.28,10.110.103.101,10.110.103.102,10.110.103.106,10.110.103.107,10.110.103.108,10.110.103.3,10.110.103.4,10.110.103.6,10.110.103.11,10.110.103.12,10.110.103.14,10.110.103.19,10.110.103.20,10.110.103.21,10.110.103.22,10.110.103.23,10.110.103.26,10.110.103.28,10.110.103.101,10.110.103.102,10.110.103.106,10.110.103.107,10.110.103.108,10.110.103.3,10.110.103.4,10.110.103.6,10.110.103.11,10.110.103.12,10.110.103.14,10.110.103.19,10.110.103.20,10.110.103.21,10.110.103.22,10.110.103.23,10.110.103.26,10.110.103.28,10.110.103.101,10.110.103.102,10.110.103.106,10.110.103.107,10.110.103.108', 'copy', 'src=/root/disk.sh dest=/tmp/disk.sh', 10)
    single_task = AdHocSingleTask('10.110.31.5,10.110.31.6,10.110.31.7,10.110.31.8,10.110.31.9,10.110.31.10,10.110.31.11,10.110.31.12,10.110.31.13', 'shell', 'rm -f /tmp/fstab', 300)
    single_task.exec_adhoc_task()
