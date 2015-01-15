#!/usr/bin/env python
# -*- coding: utf-8 -*-
from learn import db

__author__ = 'Lynch'

import time
import uuid
import logging

from learn.orm import Model, StringField, FloatField


def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)


class User(Model):
    __table__ = 'user'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    email = StringField(updatable=False, ddl='varchar(50)')
    password = StringField(ddl='varchar(50)')
    name = StringField(ddl='varchar(50)')
    image = StringField(ddl='varchar(500)')
    created_at = FloatField(updatable=False, default=time.time)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    db.create_engine('python', '123456', 'python_web')
    db.execute('drop table if exists user')
    db.execute('CREATE TABLE `user` ('
               '`id` varchar(50) NOT NULL,'
               '`name` varchar(50) DEFAULT NULL,'
               '`password` varchar(50) DEFAULT NULL,'
               '`email` varchar(50) DEFAULT NULL,'
               '`image` varchar(50) DEFAULT NULL,'
               '`created_at` bigint,'
               'PRIMARY KEY (`id`)'
               ') ENGINE=InnoDB DEFAULT CHARSET=utf8;')
    user = User(name='Lynch', email='lynch.shanghai@gmail.com', password='123456', image='')
    user.insert()
    print 'new user id:', user.id
    user = user.find_one(user.id)
    print 'find user: ', user