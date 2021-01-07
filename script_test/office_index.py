# coding: utf-8
"""
@Author: Robby
@Module name: office_index.py
@Create date: 2020-09-10
@Function: 
"""


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import shutil

# 导入ansible的核心类
import ansible.constants as C
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.module_utils.common.collections import ImmutableDict
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.vars.manager import VariableManager
from ansible import context





def main():
    # 定义主机列表
    host_list = ['10.110.119.5',]

    # 将主机列表转换为主机字符串
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
                                    gathering=False,)

    # 创建loader
    loader = DataLoader()

    # 指定密码使用口令
    passwords = dict(vault_pass='secret')

    # 指定自定义的回调类，copy模块
    # results_callback = CopyModuleJSONCallback()
    # 指定回调类shell模块
    results_callback = ShellModuleJsonCallback()

    # 创建资产对象
    inventory = InventoryManager(loader=loader, sources=sources)

    # 添加资产变量
    variable_manager = VariableManager(loader=loader, inventory=inventory)
    variable_manager.set_host_variable(host='10.110.119.5', varname='ansible_ssh_user', value='ipfsmain')
    variable_manager.set_host_variable(host='10.110.119.5', varname='ansible_ssh_pass', value='ipfsmain')
    variable_manager.set_host_variable(host='10.110.119.5', varname='ansible_sudo_pass', value='ipfsmain')
    variable_manager.set_host_variable(host='10.110.119.5', varname='ansible_python_interpreter', value='/usr/bin/python3')

    # 创建任务队列管理器
    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variable_manager,
        loader=loader,
        passwords=passwords,
        stdout_callback=results_callback,
    )


    # 定义需要执行的任务
    play_source = dict(
        name="Ansible Play",
        hosts=host_list,
        gather_facts='no',
        tasks=[
            dict(action={'module': 'shell', 'args': 'mkdir -pv /root/hello'}),
            # dict(action={'module': 'shell', 'args': 'chown -R root.root /root/hello'}),
            dict(action={'module': 'shell', 'args': 'rm -fr /root/hello'}),
            # dict(action={'module': 'copy', 'args': 'src=/etc/fstab dest=/tmp/'}),
            # dict(action={'module': 'shell', 'args': 'apt remove -y apach2'}),
            # dict(action={'module': 'ping'}),
            # dict(action=dict(module='shell', args='ls'), register='shell_out'),
            # dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}'))),
            # dict(action=dict(module='command', args=dict(cmd='/usr/bin/uptime'))),
        ]
    )

    # 创建play对象
    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    # 在任务队列中执行play对象
    try:
        result = tqm.run(play)  # most interesting data for a play is actually sent to the callback's methods
    finally:
        # 每次执行完毕后，清理任务队列中的任务
        tqm.cleanup()
        if loader:
            loader.cleanup_all_tmp_files()

    # Remove ansible tmpdir，清理临时目录
    shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

    print("UP ***********")
    for host, result in results_callback.host_ok.items():
        print(result)
        print(result._result)
        print('{0} >>> {1}'.format(host, result._result['stdout']))

    print("FAILED *******")
    for host, result in results_callback.host_failed.items():
        print('{0} >>> {1}'.format(host, result._result['stderr']))

    print("DOWN *********")
    for host, result in results_callback.host_unreachable.items():
        print('{0} >>> {1}'.format(host, result._result['msg']))


if __name__ == '__main__':

    main()