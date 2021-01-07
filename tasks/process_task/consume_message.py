# coding: utf-8
"""
@Author: Robby
@Module name: consume_message.py
@Create date: 2020-12-21
@Function: 
"""


import json
from multiprocessing import Event
import multiprocessing
from threading import Thread

from kafka import  TopicPartition, OffsetAndMetadata

from utils.parse_file import KafkaProducerConsumerSingleton, FlagSingleton, ProcessExecInterval
from execute_api.adhoc.cmd_api import AdHocSingleTask
from execute_api.playbook.playbook_api import PlaybookSingleTask
from utils.const_file import CONSUMER_INFO_LOG, CONSUMER_ERROR_LOG, SUBPROCESS_LOG
from utils.global_logger import getlogger

consumer_logger = getlogger('consumer_logger', CONSUMER_INFO_LOG, CONSUMER_ERROR_LOG)
subprocess_logger = getlogger(logger_name='subprocess', info_file_path=SUBPROCESS_LOG, error_file_path=SUBPROCESS_LOG)

# 执行adhoc ansible任务
def exec_adhoc_function(ip, module, args, timeout):
    if not timeout:
        timeout = 100
    consumer_logger.info('Adhoc Arguments: {}'.format((ip, module, args, timeout), ))
    adhoc_task = AdHocSingleTask(ip, module, args, timeout)
    adhoc_task.exec_adhoc_task()

# 执行playbook ansible任务
def exec_playbook_function(ip, playbook_content, playbook_name, playbook_timeout):

    if not playbook_timeout:
        playbook_timeout = 600
    consumer_logger.info('Playbook Arguments: {}'.format((ip, playbook_content, playbook_name, playbook_timeout), ))
    playbook_task = PlaybookSingleTask(ip, playbook_content, playbook_name, playbook_timeout)
    playbook_task.exec_playbook_task()

# 消费kafka指令
def consume_kafka_message(event: Event):
    consumer = KafkaProducerConsumerSingleton._get_consumer()
    interval = ProcessExecInterval._get_exec_engine_interval()

    while not event.wait(int(interval)):
        subprocess_logger.info('Current Process is : {}'.format(multiprocessing.current_process().name))

        try:
            consumer_logger.info("Try to consume Kafka Message......")

            for message in consumer:  # 这里是卡死的，有数据消费才会往下走
                # 当消费了第一条数据后，进入循环体
                while not event.wait(int(interval)):
                    # 获取当前的flag
                    flag = FlagSingleton._get_flag()
                    subprocess_logger.info('flag is : {}'.format(flag))
                    # 如果flag为Ture，说明可用执行任务
                    if flag:
                        # 获取指令
                        bytes_data = message.value
                        # 指令加载
                        json_data = bytes_data.decode()
                        dict_data = json.loads(json_data)
                        # 获取指令类型
                        type = dict_data.get('type')
                        consumer_logger.info('type={} message={}'.format(type, json_data))

                        # 开始执行任务
                        if type == 'adhoc':
                            args = dict_data.get('ip'), dict_data.get('module'), dict_data.get(
                                'args'), dict_data.get('timeout')
                            consumer_logger.info('Begine to Exec Adhoc, args={}'.format(args, ))
                            Thread(target=exec_adhoc_function, args=args, name='adhoc', ).start()
                            consumer_logger.info('End Exec Adhoc')
                            # 设置不可执行任务, 等待执行完毕
                            FlagSingleton._set_flag(False)
                            # 下面这几行不能与【if flag】在同一列，必须写在这里
                            new_offset = message.offset + 1
                            consumer_logger.info('Current Offset={}, New Offset={}'.format(message.offset, new_offset))
                            tp = TopicPartition(message.topic, message.partition)
                            consumer.commit(offsets={tp: (OffsetAndMetadata(new_offset, None))})
                            consumer_logger.info('Commit Offset: Ok')
                            break

                        elif type == 'playbook':
                            args = dict_data.get('ip'), dict_data.get('playbook_content'), dict_data.get(
                                'playbook_name'), dict_data.get('timeout')
                            consumer_logger.info('Begine to Exec Playbook, args={}'.format(args, ))
                            Thread(target=exec_playbook_function, args=args, name='playbook', ).start()
                            consumer_logger.info('End Exec Playbook')
                            FlagSingleton._set_flag(False)
                            new_offset = message.offset + 1
                            consumer_logger.info('Current Offset={}, New Offset={}'.format(message.offset, new_offset))
                            tp = TopicPartition(message.topic, message.partition)
                            consumer.commit(offsets={tp: (OffsetAndMetadata(new_offset, None))})
                            consumer_logger.info('Commit Offset: Ok')
                            break

                        else:
                            consumer_logger.error('Kafka Message type Error：type={}'.format(type))
                            new_offset = message.offset + 1
                            consumer_logger.info('Current Offset={}, New Offset={}'.format(message.offset, new_offset))
                            tp = TopicPartition(message.topic, message.partition)
                            consumer.commit(offsets={tp: (OffsetAndMetadata(new_offset, None))})
                            consumer_logger.info('Commit Offset: Ok')
                            break



        except Exception as e:
            consumer_logger.error('Consume Kafka Message Error：{}'.format(e))


if __name__ == '__main__':
    consume_kafka_message(Event())