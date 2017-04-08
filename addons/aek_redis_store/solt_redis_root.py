# -*- coding: utf-8 -*-

try:
    import psutil
except ImportError:
    psutil = None

from openerp.tools.func import lazy_property


import logging

import openerp
from openerp import tools, http

from werkzeug.contrib.sessions import SessionStore

import redis

import cPickle

_logger = logging.getLogger(__name__)


class RedisSessionStore(SessionStore):
    def __init__(self, session_class=None, key_prefix=''):
        SessionStore.__init__(self, session_class=session_class)
        self.redis = redis.Redis(tools.config.get('redis_host', 'localhost'), 
                                 int(tools.config.get('redis_port', 6379)), 
                                 int(tools.config.get('redis_dbindex', 1)), 
                                 password=tools.config.get('redis_pass', None))
        self.path = openerp.tools.config.session_dir
        self.expire = int(tools.config.get('redis_session_expire', 1800))
        self.key_prefix = key_prefix
        
    def save(self, session):
        key = self._get_session_key(session.sid)
        data = cPickle.dumps(dict(session))
        self.redis.setex(key, data, self.expire)

    def delete(self, session):
        key = self._get_session_key(session.sid)
        self.redis.delete(key)
    
    def _get_session_key(self,sid):
        key = self.key_prefix + sid
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        return key
    
    def get(self, sid):
        key = self._get_session_key(sid)
        data = self.redis.get(key)
        if data:
            self.redis.setex(key, data, self.expire)
            data = cPickle.loads(data)
            return self.session_class(data, sid, False)
        return self.session_class({'db': False}, sid, False)


# if tools.config.get('redis_store', False):
#     http.root.session_store = RedisSessionStore(session_class=http.OpenERPSession)

# vim:et:ts=4:sw=4:
