# coding: utf-8
"""
@Author: Robby
@Module name: playbook_api.py
@Create date: 2020-12-25
@Function: 封装playbook接口
"""
import shutil
import time
import os

import ansible.constants as C
from ansible.module_utils.common.collections import ImmutableDict
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible import context
from ansible.executor.playbook_executor import PlaybookExecutor
from utils.const_file import PLAYBOOK_DIR, PLAYBOOK_ERROR_LOG, PLAYBOOK_INFO_LOG, SQL_INFO_LOG, SQL_ERROR_LOG
from func_timeout import func_timeout, FunctionTimedOut
from utils.global_logger import getlogger
from execute_api.custom_callback.playbook_callback import PlaybookCallback
from utils.parse_file import MySQLSessionSingleton, AnsibleConfigSingleton
from model import playbook as playbook_model
from utils.parse_file import FlagSingleton




playbook_logger = getlogger('playbook', PLAYBOOK_INFO_LOG, PLAYBOOK_ERROR_LOG)
sql_logger = getlogger('sql', SQL_INFO_LOG, SQL_ERROR_LOG)
ssh_user, ssh_password, ssh_sudo_password =  AnsibleConfigSingleton._get_ansible_config_info()

class PlaybookSingleTask:
    __loader = None
    __callback = None
    __inventory = None
    __variable_manager = None

    def __init__(self, host: str, playbook: str, playbook_name: str, exec_timeout=600, ssh_user=ssh_user, ssh_password=ssh_password, ssh_sudo_password=ssh_sudo_password, python_interpreter='/usr/bin/python3',):
        self.host = host
        self.playbook = playbook
        self.playbook_name = playbook_name
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
                                        remote_user=None,
                                        remote_port=None,
                                        private_key_file=None,
                                        module_path=None,
                                        become=True,
                                        become_method='sudo',
                                        become_user='root',
                                        verbosity=3,
                                        listhosts=None,
                                        listtasks=None,
                                        listtags=None,
                                        syntax=None,
                                        forks=10,
                                        poll_interval=15,
                                        start_at_task=None, )

        return sources

    def __get_loader(self):
        if self.__loader == None:
            self.__loader = DataLoader()
        return self.__loader

    def __get_callback(self):
        if self.__callback == None:
            self.__callback = PlaybookCallback()
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

    def __get_playbook_file(self):
        playbook_str = self.playbook.replace('target_hosts', self.host.replace(' ', '').strip(','))
        with open(os.path.join(PLAYBOOK_DIR, self.playbook_name), 'w') as f_write:
            f_write.write(playbook_str)

    def exec_playbook_task(self):

        self.__get_playbook_file()
        playbook = PlaybookExecutor(playbooks=[os.path.join(PLAYBOOK_DIR, self.playbook_name)],
                                    inventory=self.__get_inventory(),
                                    variable_manager=self.__get_variable_manager(),
                                    loader=self.__get_loader(),
                                    passwords=dict(vault_pass='secret'))

        playbook._tqm._stdout_callback = self.__get_callback()

        try:
            func_timeout(int(self.exec_timeout), playbook.run, )

        except FunctionTimedOut as e:
            playbook_logger.error('Playbook Timeout Error: hosts={} playbook={} message={}'.format(self.host, self.playbook, e))

            session = MySQLSessionSingleton._get_mysql_session()
            try:

                for host in self.host.replace(' ', '').strip(',').split(','):
                    asset_instance = session.query(playbook_model.PlaybookAsset)\
                                            .filter(playbook_model.PlaybookAsset.ip == host)\
                                            .order_by(playbook_model.PlaybookAsset.id.desc())\
                                            .first()

                    if asset_instance.result_table:
                        asset_instance.result_table = ','.join([asset_instance.result_table, playbook_model.PlaybookExecTimeout.__tablename__])
                    else:
                        asset_instance.result_table = playbook_model.PlaybookExecTimeout.__tablename__


                    exec_timeout_instance = playbook_model.PlaybookExecTimeout(asset_id=asset_instance.id)
                    session.add(exec_timeout_instance)
                    session.commit()

            except Exception as e:
                sql_logger.error('SQL Error: '.format(e))
                session.rollback()

            finally:
                session.close()

        except Exception as e:
            playbook_logger.error('Playbook EXEC Error: {}'.format(e))

        finally:
            playbook._tqm.cleanup()
            loader = self.__get_loader()
            if loader:
                loader.cleanup_all_tmp_files()
            # 移除ansible tmp 目录
            shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)
            time.sleep(1)
            FlagSingleton._set_flag(True)


if __name__ == '__main__':
    ip = '10.110.31.1,10.110.31.2'
    playbook_content = '\n- hosts: target_hosts\n  become: yes\n  gather_facts: false\n  tasks:\n  - name: create dir\n    shell: mkdir /root/hello\n\n  - name: create file in dir\n    shell: touch /root/hello/hello.txt\n\n  - name: 安装apache2\n    shell: hello\n'
    playbook_name = 'deploy-agent'
    playbook_timeout = 600

    playbook_task = PlaybookSingleTask(ip, playbook_content, playbook_name, playbook_timeout)
    playbook_task.exec_playbook_task()