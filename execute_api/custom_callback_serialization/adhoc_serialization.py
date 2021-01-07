# coding: utf-8
"""
@Author: Robby
@Module name: adhoc_serialization.py
@Create date: 2020-12-11
@Function: 获取AdHoc回调对象，将结果序列化后入库
"""

from execute_api.custom_callback.adhoc_callback import AdHocCallback
from utils.parse_file import MySQLSessionSingleton
from model import adhoc
from utils.global_logger import getlogger
from utils.const_file import SQL_INFO_LOG, SQL_ERROR_LOG

sql_logger = getlogger('consumer', SQL_INFO_LOG, SQL_ERROR_LOG)

# AdHoc结果集入库
def adhoc_callback_to_mysql(instance, callback: AdHocCallback):
    # 获取session
    session = MySQLSessionSingleton._get_mysql_session()


    if instance.module == 'copy':
        for host, result in callback.host_ok.items():
            # 获取IP对应的记录
            try:
                asset_instance = session.query(adhoc.Asset).filter(adhoc.Asset.ip == host).order_by(adhoc.Asset.id.desc()).first()
                result_dict = result._result
                asset_instance.result_table = adhoc.CopySuccess.__tablename__
                copy_success_instance = adhoc.CopySuccess(asset_id=asset_instance.id,
                                                          dest=result_dict.get('dest'))
                session.add(copy_success_instance)
                session.commit()

            except Exception as e:
                sql_logger.error('SQL CopySuccess Error: {}'.format(e))
                session.rollback()

            finally:
                session.close()


        for host, result in callback.host_failed.items():
            try:
                asset_instance = session.query(adhoc.Asset).filter(adhoc.Asset.ip == host).order_by(adhoc.Asset.id.desc()).first()
                result_dict = result._result
                asset_instance.result_table = adhoc.CopyFail.__tablename__
                copy_fail_instance = adhoc.CopyFail(asset_id=asset_instance.id,
                                                    msg=result_dict.get('msg'),
                                                    exception=result_dict.get('exception'),
                                                    )
                session.add(copy_fail_instance)
                session.commit()


            except Exception as e:
                sql_logger.error('SQL CopyFail Error: {}'.format(e))
                session.rollback()

            finally:
                session.close()

    elif instance.module == 'shell':
        for host, result in callback.host_ok.items():
            try:
                asset_instance = session.query(adhoc.Asset).filter(adhoc.Asset.ip == host).order_by(adhoc.Asset.id.desc()).first()
                result_dict = result._result
                asset_instance.result_table = adhoc.SHELLSuccess.__tablename__
                shell_success_instance = adhoc.SHELLSuccess(asset_id=asset_instance.id,
                                                           cmd=result_dict.get('cmd'),
                                                           stdout=result_dict.get('stdout'),
                                                           )
                session.add(shell_success_instance)
                session.commit()

            except Exception as e:
                sql_logger.error('SQL SHELLSuccess Error: {}'.format(e))
                session.rollback()

            finally:
                session.close()


        for host, result in callback.host_failed.items():
            try:
                asset_instance = session.query(adhoc.Asset).filter(adhoc.Asset.ip == host).order_by(adhoc.Asset.id.desc()).first()
                result_dict = result._result
                asset_instance.result_table = adhoc.SHELLFail.__tablename__
                shell_fail_instance = adhoc.SHELLFail(asset_id=asset_instance.id,
                                                    msg=result_dict.get('msg'),
                                                    stderr=result_dict.get('stderr'),
                                                    )
                session.add(shell_fail_instance)
                session.commit()

            except Exception as e:
                sql_logger.error('SQL SHELLFail Error: {}'.format(e))
                session.rollback()

            finally:
                session.close()


    elif instance.module == 'unarchive':
        for host, result in callback.host_ok.items():
            try:
                asset_instance = session.query(adhoc.Asset).filter(adhoc.Asset.ip == host).order_by(adhoc.Asset.id.desc()).first()
                result_dict = result._result
                asset_instance.result_table = adhoc.UNARCHIVESuccess.__tablename__
                unarchive_success_instance = adhoc.UNARCHIVESuccess(asset_id=asset_instance.id,
                                                                   dest=result_dict.get('dest'),
                                                                   )
                session.add(unarchive_success_instance)
                session.commit()

            except Exception as e:
                sql_logger.error('SQL UNARCHIVESuccess Error: {}'.format(e))
                session.rollback()

            finally:
                session.close()

        for host, result in callback.host_failed.items():
            try:
                asset_instance = session.query(adhoc.Asset).filter(adhoc.Asset.ip == host).order_by(adhoc.Asset.id.desc()).first()
                result_dict = result._result
                asset_instance.result_table = adhoc.UNARCHIVEFail.__tablename__
                unarchive_fail_instance = adhoc.UNARCHIVEFail(asset_id=asset_instance.id,
                                                              msg=result_dict.get('msg'),
                                                             )
                session.add(unarchive_fail_instance)
                session.commit()

            except Exception as e:
                sql_logger.error('SQL UNARCHIVEFail Error: {}'.format(e))
                session.rollback()

            finally:
                session.close()


    for host, result in callback.host_unreachable.items():
        try:
            asset_instance = session.query(adhoc.Asset).filter(adhoc.Asset.ip == host).order_by(adhoc.Asset.id.desc()).first()
            result_dict = result._result
            asset_instance.result_table = adhoc.UNREACHABLE.__tablename__
            unreachable_instance = adhoc.UNREACHABLE(asset_id=asset_instance.id,
                                                     msg=result_dict.get('msg'),)
            session.add(unreachable_instance)
            session.commit()

        except Exception as e:
            sql_logger.error('SQL UNREACHABLE Error: {}'.format(e))
            session.rollback()

        finally:
            session.close()