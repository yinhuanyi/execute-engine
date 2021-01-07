# coding: utf-8
"""
@Author: Robby
@Module name: ad_hoc.py
@Create date: 2020-09-10
@Function: 
"""

import os
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from pprint import pprint
from collections import namedtuple

Project_Dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

Conf_dir = os.path.join(Project_Dir, 'conf')
Hosts_yml = os.path.join(Conf_dir, 'hosts.yml')
Private_key = os.path.join(Conf_dir, 'id_rsa')


# 实例化加载器
loader = DataLoader()
# 获取inventory信息，可以获取
inventory = InventoryManager(loader=loader, sources=[Hosts_yml])
host = inventory.get_host('23.237.49.100')  # 获取单台主机

# 获取inventory的变量信息
variable_manager =VariableManager(loader=loader, inventory=inventory)


#
# 使用命名元组来使用执行选项
Options = namedtuple('Options', ['connection','module_path', 'forks', 'timeout',  'remote_user',
                'ask_pass', 'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
                'scp_extra_args', 'become', 'become_method', 'become_user', 'ask_value_pass', 'verbosity',
                'check', 'listhosts', 'listtasks', 'listtags', 'syntax','diff'])

options = Options(connection='smart', module_path=None, forks=100, timeout=10,
                remote_user='root', ask_pass=False, private_key_file=Private_key, ssh_common_args=None, ssh_extra_args=None,
                sftp_extra_args=None, scp_extra_args=None, become=True, become_method='sudo',
                become_user='root', ask_value_pass=False, verbosity=None, check=False, listhosts=False,
                listtasks=False, listtags=False, syntax=False, diff=True)


# 定义需要执行的任务， 注意任务主机必须在inventory里面
play_source = dict(
    name="ansible test",
    hosts='23.237.49.100',  # 这个IP地址必须在inventory文件中，或者这里改写为域名，但是这个域名一定要在inventory文件，且在主机的/etc/hosts文件中需要有解析
    gather_facts='no', # 是否获取主机的基本信息
    tasks=[            # 这里是一个任务列表，可以一个任务一个任务的写, 写多个任务
        dict(action={'module': 'shell', 'args': 'mkdir /root/hello'}),
    ]
)


# 使用ad-hoc模式执行任务
play = Play().load(data=play_source, variable_manager=variable_manager, loader=loader)


task_queue = TaskQueueManager(
    inventory=inventory,
    variable_manager=variable_manager,
    loader=loader,
    options=options,
    passwords=None,
)

# 执行任务，且返回result结果
task_queue.run(play)