# coding: utf-8
"""
@Author: Robby
@Module name: callback_stdout.py
@Create date: 2020-09-11
@Function: ansible命令行实现返回结果的封装
"""

from ansible.plugins.callback import CallbackBase
from ansible.plugins.callback.default import CallbackModule
from ansible.plugins.callback.minimal import CallbackModule as CMDCallBackModule



# Shell模块输出
class AdHocCallback(CallbackBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    # 节点不可达时，会调用
    def v2_runner_on_unreachable(self, result):
        host = result._host
        self.host_unreachable[host.get_name()] = result


    # 单个部署任务成功时，会调用
    def v2_runner_on_ok(self, result, *args, **kwargs):
        host = result._host
        self.host_ok[host.get_name()] = result


    # 节点的部署任务失败时，会调用
    def v2_runner_on_failed(self, result, *args, **kwargs):
        host = result._host
        self.host_failed[host.get_name()] = result


