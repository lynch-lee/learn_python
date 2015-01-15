#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Lynch'

import MySQLdb
import threading
import logging
import functools


#自定义数据库异常
class DBException(Exception):
    pass


# 数据库引擎对象
class _Engine(object):
    def __init__(self, connection):
        #lambda表达式，外层传入的创建连接函数
        self._connect = connection

    def connect(self):
        #执行创建连接函数
        return self._connect()


# 持有数据库连接的上下文对象
class _DbCtx(threading.local):
    def __init__(self, *args, **kwargs):
        super(_DbCtx, self).__init__(*args, **kwargs)
        self.connection = None
        self.transactions = 0

    #数据库连接是否初始化
    def is_init(self):
        return not self.connection is None

    def init(self):
        self.connection = _LazyConnection()
        self.transactions = 0

    def cleanup(self):
        self.connection.cleanup()
        self.connection = None


engine = None

_db_ctx = _DbCtx()


class _LazyConnection(object):
    def __init__(self):
        self.connection = None

    def cursor(self):
        if self.connection is None:
            self.connection = engine.connect()
            logging.info('open connection <%s>...' % hex(id(self.connection)))
        return self.connection.cursor()

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def cleanup(self):
        if self.connection:
            self.connection.close()
            logging.info('close connection <%s>...' % hex(id(self.connection)))
        pass

    pass


#数据库连接上下文
class _ConnectionCtx(object):
    def __enter__(self):
        global _db_ctx
        self.should_cleanup = False
        #如果连接没有初始化
        if not _db_ctx.is_init():
            #连接初始化
            _db_ctx.init()
            #设置需要清理的状态为 True
            self.should_cleanup = True
        return self

    def __exit__(self, exc_type, exc_value, trace_back):
        global _db_ctx
        #如果需要清理连接
        if self.should_cleanup:
            #清理连接
            _db_ctx.cleanup()


#初始化数据库连接
def create_engine(user, password, database, host="127.0.0.1"):
    global engine
    if engine is not None:
        logging.error("engine is already initialized.")
        raise DBException("engine is already initialized.")
    #初始化数据库引擎
    engine = _Engine(lambda: MySQLdb.connect(host, user, password, database))
    logging.info('init mysql engine <%s> ok.' % hex(id(engine)))


#定义装饰器，用于创建和释放连接
def with_connection(func):
    @functools.wraps(func)
    def _wrapper(*args, **kw):
        with _ConnectionCtx():
            return func(*args, **kw)
    return _wrapper


@with_connection
def _query(sql, *args):
    global _db_ctx
    cursor = None
    sql = sql.replace('?', '%s')
    logging.info('SQL: %s, ARGS: %s' % (sql, args))
    try:
        cursor = _db_ctx.connection.cursor()
        cursor.execute(sql, args)
        for row in cursor.fetchall():
            print row
    finally:
        if cursor is not None:
            cursor.close()


@with_connection
def _execute(sql, *args):
    global _db_ctx
    cursor = None
    sql = sql.replace('?', '%s')
    logging.info('SQL: %s, ARGS: %s' % (sql, args))
    try:
        cursor = _db_ctx.connection.cursor()
        cursor.execute(sql, args)
        r = cursor.rowcount
        if _db_ctx.transactions == 0:
            logging.info('auto commit')
            _db_ctx.connection.commit()
        return r
    finally:
        if cursor:
            cursor.close()


def query(sql, *args):
    return _query(sql, *args)


def execute(sql, *args):
    return _execute(sql, *args)