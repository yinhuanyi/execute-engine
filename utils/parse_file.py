# coding: utf-8
"""
@Author: Robby
@Module name: parse_file.py
@Create date: 2020-10-28
@Function: 全局单例
"""
import socket
from multiprocessing import Event
from configparser import ConfigParser

from kafka import KafkaProducer, KafkaConsumer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from utils.const_file import SERVER_CONFIG, SQL_ERROR_LOG, SQL_INFO_LOG
from utils.encrypt_decrypt import decrypt
from utils.global_logger import getlogger


class SingletonBase:

    __parser = None

    @classmethod
    def _get_parser(cls):
        if cls.__parser == None:
            cls.__parser = ConfigParser()
            cls.__parser.read(SERVER_CONFIG)
        return cls.__parser

# kafka配置
class KafkaConfigSingleton:
    __parser = None
    __kafka_config_info = None

    @classmethod
    def __get_parser(cls):
        if cls.__parser == None:
            cls.__parser = ConfigParser()
            cls.__parser.read(SERVER_CONFIG)
        return cls.__parser

    @classmethod
    def _get_kafka_config_info(cls):
        if cls.__kafka_config_info == None:
            parser = cls.__get_parser()
            kafka_bootstrap_servers = parser.get('Kafka_Cluster', 'BOOTSTRAP_SERVERS')
            kafka_group_id = parser.get('Kafka_Cluster', 'GROUP_ID')
            kafka_auto_offset_reset = parser.get('Kafka_Cluster', 'AUTO_OFFSET_RESET')
            kafka_topic = parser.get('Kafka_Cluster', 'TOPIC')

            cls.__kafka_config_info = kafka_bootstrap_servers, kafka_group_id, kafka_auto_offset_reset, kafka_topic

        return cls.__kafka_config_info

# kafka生产和消费者
class KafkaProducerConsumerSingleton:
    __kafka_bootstrap_servers_str = None
    __kafka_group_id = None
    __kafka_auto_offset_reset = None
    __kafka_topic = None
    __kafka_consumer = None
    __kafka_producer = None

    @classmethod
    def _get_kafka_config_info(cls, role):
        if cls.__kafka_bootstrap_servers_str == None:
            cls.__kafka_bootstrap_servers_str, cls.__kafka_group_id, cls.__kafka_auto_offset_reset, cls.__kafka_topic = KafkaConfigSingleton._get_kafka_config_info()

        if not role == 'consumer':
            return cls.__kafka_bootstrap_servers_str
        return cls.__kafka_bootstrap_servers_str, cls.__kafka_group_id, cls.__kafka_auto_offset_reset, cls.__kafka_topic


    @classmethod
    def _get_producer(cls):
        if cls.__kafka_producer == None:
            kafka_bootstrap_servers_str = cls._get_kafka_config_info('producer')
            kafka_bootstrap_servers = kafka_bootstrap_servers_str.split(',')
            cls.__kafka_producer = KafkaProducer(bootstrap_servers=kafka_bootstrap_servers, )
        return cls.__kafka_producer


    @classmethod
    def _get_consumer(cls):
        if cls.__kafka_consumer == None:
            kafka_bootstrap_servers_str, kafka_group_id, kafka_auto_offset_reset, kafka_topic = cls._get_kafka_config_info('consumer')
            kafka_bootstrap_servers = kafka_bootstrap_servers_str.split(',')
            # cls.__kafka_consumer = KafkaConsumer(kafka_topic, client_id=socket.gethostname(), group_id=kafka_group_id, auto_offset_reset=kafka_auto_offset_reset, bootstrap_servers=kafka_bootstrap_servers, enable_auto_commit=False)
            # cls.__kafka_consumer = KafkaConsumer(kafka_topic, client_id='Robby1', group_id=kafka_group_id,
            #                                      auto_offset_reset=kafka_auto_offset_reset,
            #                                      bootstrap_servers=kafka_bootstrap_servers, enable_auto_commit=False)
            cls.__kafka_consumer = KafkaConsumer(kafka_topic,
                                                 client_id=socket.gethostname(),
                                                 group_id=kafka_group_id,
                                                 auto_offset_reset=kafka_auto_offset_reset,
                                                 bootstrap_servers=kafka_bootstrap_servers,
                                                 # heartbeat_interval_ms=60 * 1000,
                                                 # session_timeout_ms=600 * 1000,
                                                 # request_timeout_ms=610 * 1000,
                                                 enable_auto_commit=False)
        return cls.__kafka_consumer

# MySQL配置
class MySQLConfigSingleton:
    __parser = None
    __mysql_config_info = None

    @classmethod
    def __get_parser(cls):
        if cls.__parser == None:
            cls.__parser = ConfigParser()
            cls.__parser.read(SERVER_CONFIG)
        return cls.__parser

    @classmethod
    def _get_mysql_config_info(cls):
        if cls.__mysql_config_info == None:
            parser = cls.__get_parser()
            mysql_ip = parser.get('Fil_EXEC_MySQL', 'IP')
            mysql_port = parser.get('Fil_EXEC_MySQL', 'PORT')
            mysql_database = parser.get('Fil_EXEC_MySQL', 'DATABASE')
            mysql_user = parser.get('Fil_EXEC_MySQL', 'USER')
            mysql_password = parser.get('Fil_EXEC_MySQL', 'PASSWORD')

            cls.__mysql_config_info = mysql_ip, mysql_port, mysql_database, mysql_user, decrypt(mysql_password)

        return cls.__mysql_config_info

# 数据库engine单例
class MySQLEngineSingleton:
    __engine = None

    @classmethod
    def _get_mysql_engine(cls):
        if cls.__engine == None:
            mysql_ip, mysql_port, mysql_database, mysql_user, mysql_password = MySQLConfigSingleton._get_mysql_config_info()
            engine = create_engine('mysql+pymysql://{user}:{password}@{mysql_ip}:{port}/{database}?charset=utf8mb4'
                                   .format(user=mysql_user, password=mysql_password, mysql_ip=mysql_ip, port=mysql_port, database=mysql_database),
                                    echo=False,
                                    pool_size=10,
                                    pool_recycle=-1,
                                    encoding='utf-8',
                                    max_overflow=3000)

            # 配置日志
            getlogger('sqlalchemy.engine', SQL_INFO_LOG, SQL_ERROR_LOG)
            cls.__engine = engine
        return cls.__engine

# 数据库session会话
class MySQLSessionSingleton:
    __Session = None

    @classmethod
    def _get_mysql_session(cls):
        if cls.__Session == None:
            from model import adhoc
            from model import playbook
            Base = SQLAlchemyBaseSingleton._get_sqlalchemy_base()
            engine = MySQLEngineSingleton._get_mysql_engine()
            Base.metadata.create_all(engine)
            cls.__Session = sessionmaker(bind=engine)

        session = cls.__Session()
        return session

# 流控标志位
class FlagSingleton:
    __flag = None

    @classmethod
    def _get_flag(cls):
        if  cls.__flag == None:
            cls.__flag = True
        return cls.__flag

    @classmethod
    def _set_flag(cls, flag: bool):
        cls.__flag = flag

# 事件单例
class EventSingleton:
    __event = None

    @classmethod
    def getEventInstance(cls):
        if  cls.__event == None:
            cls.__event = Event()
        return cls.__event

# 线程执行间隔时间
class ProcessExecInterval(SingletonBase):
    __zabbix_interval = None
    __exec_interval = None


    @classmethod
    def _get_zabbix_interval(cls):
        if cls.__zabbix_interval == None:
            parser = cls._get_parser()
            interval = parser.get('Data_Send', 'ZABBIX')
            cls.__zabbix_interval = interval
        return cls.__zabbix_interval

    @classmethod
    def _get_exec_engine_interval(cls):
        if cls.__exec_interval == None:
            parser = cls._get_parser()
            interval = parser.get('Data_Send', 'EXEC')
            cls.__exec_interval = interval
        return cls.__exec_interval

# zabbix server配置
class ZabbixServerConfigSingleton(SingletonBase):

    __zabbix_server_config_info = None

    @classmethod
    def _get_zabbix_server_config_info(cls):
        if cls.__zabbix_server_config_info == None:
            parser = cls._get_parser()
            ip = parser.get('Zabbix', 'IP')
            port = parser.get('Zabbix', 'ZABBIX_PORT')
            item = parser.get('Zabbix', 'ITEM')

            cls.__exec_interval = ip, port, item
        return cls.__exec_interval

# 数据表绑定的Base单例
class SQLAlchemyBaseSingleton:
    __Base = None

    @classmethod
    def _get_sqlalchemy_base(cls):
        if cls.__Base == None:
            cls.__Base = declarative_base()
        return cls.__Base

# ansible连接配置
class AnsibleConfigSingleton(SingletonBase):
    __ansible_config_info = None

    @classmethod
    def _get_ansible_config_info(cls):
        if cls.__ansible_config_info == None:
            parser = cls._get_parser()
            ssh_user = parser.get('Ansible', 'SSH_USER')
            ssh_password = parser.get('Ansible', 'SSH_PASSWORD')
            ssh_sudo_password = parser.get('Ansible', 'SSH_SUDO_PASSWORD')

            cls.__ansible_config_info = ssh_user, ssh_password, ssh_sudo_password
        return cls.__ansible_config_info


if __name__ == '__main__':
    print(KafkaConfigSingleton._get_kafka_config_info())
    print(KafkaProducerConsumerSingleton._get_producer())
    print(KafkaProducerConsumerSingleton._get_consumer())
    print(MySQLConfigSingleton._get_mysql_config_info())
    # MySQLEngineSingleton._get_mysql_engine()
    print(ProcessExecInterval._get_zabbix_interval())
    print(ProcessExecInterval._get_exec_engine_interval())
    print(ZabbixServerConfigSingleton._get_zabbix_server_config_info())
    print(AnsibleConfigSingleton._get_ansible_config_info())