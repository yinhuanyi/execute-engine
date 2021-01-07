# coding: utf-8
"""
@Author: Robby
@Module name: index_test.py
@Create date: 2020-09-11
@Function:  可用代码
"""

import json
import shutil

import ansible.constants as C
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.module_utils.common.collections import ImmutableDict
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.vars.manager import VariableManager
from ansible import context
from execute_api.custom_callback.adhoc_callback import AdHocCallback


host_list = ['10.110.119.5',]

context.CLIARGS = ImmutableDict(connection='smart',
                                module_path=None,
                                forks=10,
                                become=True,
                                become_method='sudo',
                                become_user='root',
                                check=False,
                                command_warnings=False,
                                deprecation_warnings=False,
                                system_warnings=False,
                                diff=False,
                                verbosity=5,)

sources = ','.join(host_list)
if len(host_list) == 1:
    sources += ','

loader = DataLoader()

passwords = dict(vault_pass='secret')

# 自定义回调结果函数
results_callback = AdHocCallback()
inventory = InventoryManager(loader=loader, sources=sources)
variable_manager = VariableManager(loader=loader, inventory=inventory)

variable_manager.set_host_variable(host='10.110.119.5', varname='ansible_ssh_user', value='ipfsmain')
variable_manager.set_host_variable(host='10.110.119.5', varname='ansible_ssh_pass', value='ipfsmain')
variable_manager.set_host_variable(host='10.110.119.5', varname='ansible_sudo_pass', value='ipfsmain')
variable_manager.set_host_variable(host='10.110.119.5', varname='ansible_python_interpreter', value='/usr/bin/python3')

tqm = TaskQueueManager(
    inventory=inventory,
    variable_manager=variable_manager,
    loader=loader,
    passwords=passwords,
    stdout_callback=results_callback,
)

# 正常任务指令
play_source = dict(
    name="Ansible Play",
    hosts=host_list,
    gather_facts='no',
    tasks=[
        dict(action={'module': 'shell', 'args': 'cat /etc/passwd | grep root'}),
    ]
)

# 加载任务指令
play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

try:
    result = tqm.run(play)
finally:
    tqm.cleanup()
    if loader:
        loader.cleanup_all_tmp_files()

# Remove ansible tmpdir
shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

print("UP ***********")
for host, result in results_callback.host_ok.items():
    print('{} >>> SUCCESS \n{}'.format(host, json.dumps(result._result, indent=4)))

print("FAILED *******")
for host, result in results_callback.host_failed.items():
    print('{} >>> FAILED \n{}'.format(host, json.dumps(result._result, indent=4)))

print("DOWN *********")
for host, result in results_callback.host_unreachable.items():
    print('{} >>> UNREACHABLE \n{}'.format(host, json.dumps(result._result, indent=4)))