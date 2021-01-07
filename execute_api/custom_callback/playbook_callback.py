# coding: utf-8
"""
@Author: Robby
@Module name: playbook_callback.py
@Create date: 2020-10-28
@Function: ansible playbook返回格式化后，写入数据库
"""

import json
from ansible.plugins.callback import CallbackBase

from utils.parse_file import MySQLSessionSingleton
from model import playbook
from utils.global_logger import getlogger
from utils.const_file import SQL_INFO_LOG, SQL_ERROR_LOG, PLAYBOOK_INFO_LOG, PLAYBOOK_ERROR_LOG

sql_logger = getlogger('consumer', SQL_INFO_LOG, SQL_ERROR_LOG)
playbook_logger = getlogger('playbook', PLAYBOOK_INFO_LOG, PLAYBOOK_ERROR_LOG)

class PlaybookCallback(CallbackBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}

    def v2_runner_on_ok(self, result, *args, **kwargs):
        session = MySQLSessionSingleton._get_mysql_session()
        host=result._host.get_name()
        result_dict = result._result
        playbook_logger.info('result={}'.format(json.dumps(result_dict, ensure_ascii=False)))


        # TODO: 这里有个问题需要思考一下：
        """
        由于获取的是最后一个IP，那么如果同一时间，这个IP执行了多次任务，这些任务分配到了多个执行引擎中
        那么多个执行引擎将会执行这个IP的任务，这个IP写入到playbook_asset表的时候，有id取反
        那么在写入这个IP的执行结果的时候，获取的是最后一个IP，会导致结果都写入到最后这个IP里面，导致结果有问题
        
        因此，前端在执行任务的时候，最好是等这个任务执行完毕后，再执行下一个，这样就能够避免结果数据写入不正确问题
        """
        asset_instance = None
        try:
            asset_instance = session.query(playbook.PlaybookAsset).filter(playbook.PlaybookAsset.ip == host).order_by(playbook.PlaybookAsset.id.desc()).first()
        except Exception as e:
            sql_logger.error('SQL PlaybookAsset Error: {}'.format(e))
            session.rollback()
            session.close()
            raise Exception('SQL PlaybookAsset Error: {}'.format(e))

        # 根据不同模块的返回结果差异来确定表
        diff = result_dict.get('diff')
        dest = result_dict.get('dest')
        cmd = result_dict.get('cmd')
        handler = result_dict.get('handler')


        if handler:
            try:
                if asset_instance.result_table:
                    asset_instance.result_table = ','.join([asset_instance.result_table, playbook.PlaybookUNARCHIVESuccess.__tablename__])
                else:
                    asset_instance.result_table = playbook.PlaybookUNARCHIVESuccess.__tablename__

                unarchive_success_instance = playbook.PlaybookUNARCHIVESuccess(asset_id=asset_instance.id,)
                session.add(unarchive_success_instance)
                session.commit()

            except Exception as e:
                sql_logger.error('SQL PlaybookUNARCHIVESuccess Error: {}'.format(e))
                session.rollback()

            finally:
                session.close()

        elif diff or dest:
            try:
                if asset_instance.result_table:
                    asset_instance.result_table = ','.join([asset_instance.result_table, playbook.PlaybookCopySuccess.__tablename__])
                else:
                    asset_instance.result_table = playbook.PlaybookCopySuccess.__tablename__

                copy_success_instance = playbook.PlaybookCopySuccess(asset_id=asset_instance.id)
                session.add(copy_success_instance)
                session.commit()

            except Exception as e:
                sql_logger.error('SQL PlaybookCopySuccess Error: {}'.format(e))
                session.rollback()

            finally:
                session.close()

        elif cmd:
            try:
                if asset_instance.result_table:
                    asset_instance.result_table = ','.join([asset_instance.result_table, playbook.PlaybookSHELLSuccess.__tablename__])
                else:
                    asset_instance.result_table = playbook.PlaybookSHELLSuccess.__tablename__

                shell_success_instance = playbook.PlaybookSHELLSuccess(asset_id=asset_instance.id,)
                session.add(shell_success_instance)
                session.commit()

            except Exception as e:
                sql_logger.error('SQL PlaybookSHELLSuccess Error: {}'.format(e))
                session.rollback()

            finally:
                session.close()



    def v2_runner_on_failed(self, result, *args, **kwargs):
        session = MySQLSessionSingleton._get_mysql_session()
        host=result._host.get_name()
        result_dict = result._result
        playbook_logger.info('result={}'.format(json.dumps(result_dict, ensure_ascii=False)))

        asset_instance = None
        try:
            asset_instance = session.query(playbook.PlaybookAsset).filter(playbook.PlaybookAsset.ip == host).order_by(playbook.PlaybookAsset.id.desc()).first()
        except Exception as e:

            sql_logger.error('SQL PlaybookAsset Error: {}'.format(e))
            session.rollback()
            session.close()
            raise Exception('SQL PlaybookAsset Error: {}'.format(e))


        msg = result_dict.get('msg')
        exception = result_dict.get('exception')
        cmd = result_dict.get('cmd')

        if msg and exception:
            try:
                if asset_instance.result_table:
                    asset_instance.result_table = ','.join([asset_instance.result_table, playbook.PlaybookCopyFail.__tablename__])
                else:
                    asset_instance.result_table = playbook.PlaybookCopyFail.__tablename__

                copy_fail_instance = playbook.PlaybookCopyFail(asset_id=asset_instance.id)
                session.add(copy_fail_instance)
                session.commit()

            except Exception as e:
                sql_logger.error('SQL PlaybookCopyFail Error: {}'.format(e))
                session.rollback()

            finally:
                session.close()

        elif msg and cmd:
            try:
                if asset_instance.result_table:
                    asset_instance.result_table = ','.join([asset_instance.result_table, playbook.PlaybookSHELLFail.__tablename__])
                else:
                    asset_instance.result_table = playbook.PlaybookSHELLFail.__tablename__
                shell_fail_instance = playbook.PlaybookSHELLFail(asset_id=asset_instance.id,)
                session.add(shell_fail_instance)
                session.commit()

            except Exception as e:
                sql_logger.error('SQL PlaybookSHELLFail Error: {}'.format(e))
                session.rollback()

            finally:
                session.close()

        elif msg:
            try:
                if asset_instance.result_table:
                    asset_instance.result_table = ','.join([asset_instance.result_table, playbook.PlaybookUNARCHIVEFail.__tablename__])
                else:
                    asset_instance.result_table = playbook.PlaybookUNARCHIVEFail.__tablename__

                unarchive_fail_instance = playbook.PlaybookUNARCHIVEFail(asset_id=asset_instance.id,)
                session.add(unarchive_fail_instance)
                session.commit()

            except Exception as e:
                sql_logger.error('SQL PlaybookUNARCHIVEFail Error: {}'.format(e))
                session.rollback()

            finally:
                session.close()


    def v2_runner_on_unreachable(self, result):
        session = MySQLSessionSingleton._get_mysql_session()
        host=result._host.get_name()
        result_dict = result._result
        playbook_logger.info('result={}'.format(json.dumps(result_dict, ensure_ascii=False)))

        asset_instance = None
        try:
            asset_instance = session.query(playbook.PlaybookAsset).filter(playbook.PlaybookAsset.ip == host).order_by(playbook.PlaybookAsset.id.desc()).first()
        except Exception as e:

            sql_logger.error('SQL PlaybookAsset Error: {}'.format(e))
            session.rollback()
            session.close()
            raise Exception('SQL PlaybookAsset Error: {}'.format(e))


        try:
            if asset_instance.result_table:
                asset_instance.result_table = ','.join([asset_instance.result_table, playbook.PlaybookUNREACHABLE.__tablename__])
            else:
                asset_instance.result_table = playbook.PlaybookUNREACHABLE.__tablename__
            unreachable_instance = playbook.PlaybookUNREACHABLE(asset_id=asset_instance.id,)
            session.add(unreachable_instance)
            session.commit()

        except Exception as e:
            sql_logger.error('SQL PlaybookUNREACHABLE Error: {}'.format(e))
            session.rollback()

        finally:
            session.close()