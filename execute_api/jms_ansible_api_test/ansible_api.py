#!/usr/bin/env python  
#-*- coding:utf-8 _*-  
""" 
@Author: Robby
@Module name: ansible_command_line_collector.py 
@Create date: 2018-09-02 
@Function：ad-hoc 模式的api接口汇聚
"""
from collections import namedtuple
import json
from ansible.inventory.host import Host,Group

from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.playbook.play import Play
from ansible import constants as C
from ansible.plugins.callback import CallbackBase
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.utils.display import logger
import logging
import os,django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'Metric_Server.settings')
django.setup()
ansible_logger = logging.getLogger('ansible_error')

from module_scripts.cfg.const_file import Ansible_Inventory_File, Secret_File
from tools.sorted_file import YamlFileSorted
from cfg.const_file import Playbook_dir

# Todo: 如果脚本测试，需要调用Django环境

class MyInventory:
    """
    这里先从ansbile的yml文件中读取资产信息，已经资产变量
    在调用任务的时候，确保Django的Asset中读取的资产名称与ansible的yml文件的资产文件一一对应

    调用方式：
    my_inventory = MyInventory()
    my_inventory.loader
    my_inventory.inventory
    my_inventory.variable_manager
    my_inventory.get_options() # 返回一个命名元组 options，可以在TaskQueueManager中直接使用
    """
    def __init__(self):
        self.loader = DataLoader() # 获取加载器
        self.inventory = InventoryManager(loader=self.loader, sources=[Ansible_Inventory_File]) # 获取资产
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory) # 获取资产变量
        self.options = None # 获取ansible ad-hoc参数


    # 获取ad-hoc模式参数
    def get_options(self, forks=10, private_key_file=Secret_File):
        Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'timeout', 'remote_user','ask_sudo_pass' ,'ask_pass',
                                         'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
                                         'scp_extra_args', 'become', 'become_method', 'become_user', 'ask_value_pass',
                                         'verbosity', 'check', 'listhosts', 'listtasks', 'listtags', 'syntax', 'diff'])


        return Options(connection='smart', module_path=None, forks=forks, timeout=10, remote_user='root', ask_sudo_pass=False, ask_pass=False, private_key_file=private_key_file, ssh_common_args=None,ssh_extra_args=None,sftp_extra_args=None, scp_extra_args=None, become=True, become_method='sudo',become_user='root', ask_value_pass=False, verbosity=None, check=False, listhosts=False,listtasks=False, listtags=False, syntax=False, diff=True)


    # 预留添加资产组接口
    def add_group(self, hostname, groupname, groupvars=None):
        pass

    # 预留添加资产接口
    def add_host(self, hostname, groupname, hostvars=None):
        pass



# 自定义命令行回调
class CommandResultCollector(CallbackBase):
    '''
    自定义回调类的使用方式:
    回调封装的是字典，返回的是字典嵌套
    callback = CommandResultCollector()

    if callback.host_ok != dict():
        for hostname, key in callback.host_ok.items():
            print('{} is {}'.format(hostname, 'successful'))
    else:
        for hostname, key in callback.host_failed.items():
            print('{} is {}'.format(hostname, 'failed'))
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}
        self.host_skip = {}


    # 获取当前主机是否不可达
    def v2_runner_on_unreachable(self, result):
        # result._host.get_name() 是获取执行任务的主机名
        # result参数是返回的是：是否主机不可达的结果
        self.host_unreachable[result._host.get_name()] = result._result

    # 获取任务是否OK
    def v2_runner_on_ok(self, result):
        self.host_ok[result._host.get_name()] = result._result

    # 获取任务是否Failed
    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.host_failed[result._host.get_name()] = result._result

    # 获取任务是否没有改变主机的配置
    def v2_runner_on_skipped(self, result):
        self.host_skip[result._host.get_name()] = result._result


# playbook自定义回调
class PlaybookResultCollector(CallbackBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.task_group_name = ""
        self.task_name = ""
        self.host_name = ""
        # task_summary = {'BRT-E35-NY-10G': {'ok': 1, 'failures': 0, 'unreachable': 0, 'changed': 1, 'skipped': 0}}
        self.task_summary = {}
        self.unmatched_host_info = ""
        self.host_ok_info = None
        self.host_unreachable = {}
        self.host_failed = {}
        self.host_skip = {}
        self.no_hosts_matched = None

    def v2_runner_on_unreachable(self, result):
        self.host_unreachable[result._host.get_name()] = result._result

    # 获取任务是否OK
    def v2_runner_on_ok(self, result):
        self.host_ok[result._host.get_name()] = result._result

    # 获取任务是否Failed
    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.host_failed[result._host.get_name()] = result._result

    # 获取任务是否没有改变主机的配置
    def v2_runner_on_skipped(self, result):
        self.host_skip[result._host.get_name()] = result._result

    # 主机playbook中的无法匹配到资产的名称
    def v2_playbook_on_no_hosts_matched(self):
        self.no_hosts_matched = "Eagle Task Error:[No Hosts Matched, Please Check Your Playbook And Inventory File]"

    #
    def v2_playbook_on_task_start(self, task, is_conditional):
        self.task_name = task

    def v2_playbook_on_play_start(self, play):
        self.task_group_name = play

    # 这里获取一个hosts列表
    # 资产文件中只有一个主机
    def v2_playbook_on_stats(self, stats):
        hosts = sorted(stats.processed.keys())
        if hosts:
            self.host_name = host = hosts[0]
            self.task_summary['{}'.format(host)] = stats.summarize(host)


    def gather_result(self, result):
        print('gather_result res======={}'.format(result))

    def gather_item_result(self, result):
        print('gather_item_result result========{}'.format(result))


    def v2_runner_item_on_ok(self, result):
        print('v2_runner_item_on_ok    result======{}'.format(result))

    def v2_runner_item_on_failed(self, result):
        print('v2_runner_item_on_failed    result======{}'.format(result))

    def setdefault(self, result):
        print('v2_runner_item_on_skipped    result======{}'.format(result))



# 执行任务
class AnsibleExecutor:
    def __init__(self, redisKey=None, logId=None, *args, **kwargs):
        self.loader = None
        self.inventory = None
        self.variable_manager = None
        self.options = None
        self.passwords = None
        self.command_line_callback = None
        self.playbook_callback = None
        self.task_queue = None
        self.redisKey = redisKey
        self.logId = logId
        self.__init_Inventory_callback()

    # 指定ansible的执行options且赋值给MyInventory
    def __init_Inventory_callback(self):
        my_inventory = MyInventory()
        C.HOST_KEY_CHECKING = False
        C.RETRY_FILES_ENABLED = False


        self.loader = my_inventory.loader
        self.inventory = my_inventory.inventory
        self.variable_manager = my_inventory.variable_manager
        self.options = my_inventory.get_options()
        self.command_line_callback = CommandResultCollector()
        self.playbook_callback = PlaybookResultCollector()

    # 以命令行的方式执行任务
    def run_command_line(self, module_name, module_args, hostname=None, extra_vars=None):
        # todo: 如果extra_vars有值的话，那么将变量交给variable_manager管理, 这个功能在服务器部署的时候调用template模块
        if extra_vars:
            self.variable_manager.extra_vars = extra_vars
        play_source = dict(
            name="{}".format(hostname),
            hosts=hostname, # todo: 这里是可以传递一个列表的，例如：['E35_brt', 'E36_brt', 'E37_brt']
            gather_facts='no',
            tasks=[
                dict(action=dict(module=module_name, args=module_args))
            ],
        )

        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)

        try:
            self.task_queue = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
                stdout_callback=self.command_line_callback,)

            self.task_queue.run(play)
        except Exception as e:
            logger.error('commandline: {}'.format(e))
            return False
            # DsRedis.OpsAnsibleModel.lpush(self.redisKey,data=err)
            # if self.logId:AnsibleSaveResult.Model.insert(self.logId, err)
        finally:
            if self.task_queue is not None:
                self.task_queue.cleanup()

    # 以ansible playbook的方式执行任务
    def run_playbook(self, playbook_path, extra_vars=None):
        try:
            # todo: 如果extra_vars有值的话，那么将变量交给variable_manager管理, 这个功能在服务器部署的时候调用template模块
            if extra_vars:
                self.variable_manager.extra_vars = extra_vars

            play_book = PlaybookExecutor(playbooks=[playbook_path],
                                         inventory=self.inventory,
                                         variable_manager=self.variable_manager,
                                         loader=self.loader,
                                         options=self.options,
                                         passwords=None,)
            play_book._tqm._stdout_callback = self.playbook_callback
            play_book.run()
        except Exception as e:
            logger.error('playbook: {}'.format(e))
            return False

    # 获取到ansible命令行的结果
    def get_command_line_result(self):
        if self.command_line_callback.host_ok != dict():
            for hostname, key in self.command_line_callback.host_ok.items():
                # self.task_result.hostname = hostname
                print(key)
                # self.task_result.cmd = key['cmd']
                # self.task_result.status = 'successful'
                # self.task_result.datetime = key['end']
        else:
            for hostname, key in self.command_line_callback.host_failed.items():
                # self.task_result.hostname = hostname
                print(key)
                # self.task_result.cmd = key['cmd']
                # self.task_result.status = 'failed'
                # self.task_result.datetime = key['end']

        # return self.task_result
        return self.playbook_callback.host_failed.items()

    # 获取到ansible playbook的结果
    def get_playbook_result(self):


        print(self.playbook_callback)


        if self.playbook_callback.host_ok != dict():
            for hostname, key in self.playbook_callback.host_ok.items():
                # self.task_result.hostname = hostname
                print('host_ok != dict() 任务成功------------------{}'.format(key))
                print(type(key))
                print("json-------------{}".format(json.dumps(key)))
        else:
            for hostname, key in self.playbook_callback.host_failed.items():
                # self.task_result.hostname = hostname
                print('host_ok == dict()  任务失败------------------{}'.format(key))
                print(type(key))

                print("json-------------{}".format(json.dumps(key)))
        return None



if __name__ == '__main__':
    # 获取执行器
    yaml_file_sorted = YamlFileSorted()
    sorted_playbook_names = yaml_file_sorted.parse_file_path(Playbook_dir)
    sorted_playbook_path = [os.path.join(Playbook_dir, name) for name in sorted_playbook_names]
    for playbook_path in sorted_playbook_path:
        executor = AnsibleExecutor(redisKey='1')

        # # command line
        # executor.run_command_line(module_name='shell', module_args='mkdir /root/hello', hostname=['BRT-E35-NY-10G', 'BRT-E48-NY-10G', 'BRT-E53-NY-10G'],)
        # result = executor.get_command_line_result()
        # print('hostname :{} cmd: {}, status: {}, datetime: {}'.format(result.hostname, result.cmd, result.status, result.datetime))

        # ansible_sudo_pass='b7ddf3497-01df-4788-b21b-11reewrbe758'   host_name=BRT-E35-NY-10G
        # playbook

        executor.run_playbook(playbook_path, extra_vars={'host_name': 'BRT-E35-NY-10G'})
        result = executor.get_playbook_result()

        # print('hostname :{} cmd: {}, status: {}, datetime: {}'.format(result.hostname, result.cmd, result.status,result.datetime))
        # print('Self Result: {}'.format(result))

