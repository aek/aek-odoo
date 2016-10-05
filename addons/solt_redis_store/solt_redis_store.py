import redis
import logging

from openerp.osv import fields, osv
import openerp.pooler as pooler
from openerp import tools

import openerp
from redis.exceptions import ConnectionError

_logger = logging.getLogger(__name__)

redis_services = {}

class RedisService(object):
    
    def __init__(self, name, host = 'localhost', port = 6379, dbindex =1 , password = None):
        if not name.startswith('redis.'):
            raise Exception('ConceptionError, bad name for Redis Service, should start with "redis."')
        self.name = name
        self.host = host
        self.port = port
        self.dbindex = dbindex
        self.password = password
        self._channel = {}
        
        try:
            self._redis = redis.Redis(host, port, dbindex , password = password, socket_timeout=5)
            if self._redis.ping():
                self.active = True
            else:
                self.active = False
        except Exception,e:
            self._redis = None
            self.active = False

        redis_services[name] = self
        
    def cursor(self):
        if self.active:
            return self._redis
        else:
            try:
                self._redis.ping()
                self.active = True
                return self._redis
            except ConnectionError:
                raise openerp.osv.osv.except_osv("Connection Error", "Not Connected to Redis")
    
    def listener(self, channel_name):
        self.subscriber.subscribe(channel_name)
        try:
            try:
                while True:
                    for msg in self.subscriber.listen():
                        _logger.info('Message received in Redis channel with data: %s' % (msg))
                        self.on_channel_receive(msg)
            except redis.ConnectionError, e:
                if e.message not in EXPECTED_CONNECTION_ERRORS:
                    _logger.info('Caught `%s`, will quit now', e.message)
                    raise
        except KeyboardInterrupt:
            pass
        
    def add_channel(self, channel_name):
        self._channel[channel_name] = self._redis.pubsub()
        
    def on_channel_receive(self, message):
        db_data = message.get('data')
        pooler.get_pool(cr.dbname).get(self.table)
        
        
class solt_redis_store(osv.osv):
    _name = 'solt.redis.store'
    _description = 'Redis Store'
    
    def _register_hook(self, cr):
        cr.execute("SELECT * FROM solt_redis_store ORDER BY id")
        result = cr.dictfetchall()

        for serv in result:
            if redis_services.has_key('redis.'+serv['name']):
                continue
            service = RedisService('redis.'+serv['name'], serv['host'], serv['port'], serv['dbindex'], serv['password'])
            cr.execute("SELECT id, name FROM solt_redis_channel where redis_conn = %s ORDER BY id" % serv['id'])
            channel_data = cr.dictfetchall()
            for channel in channel_data:
                if service._channels.has_key(channel['name']):
                    continue
                service.add_channel(channel['name'])
        return True
    
    def create(self, cr, uid, vals, context=None):
        res = osv.osv.create(self, cr, uid, vals, context)
        serv = self.browse(cr, uid, res, context)
        RedisService('redis.'+serv.name, serv.host, serv.port, serv.dbindex, serv.password)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = True
        if not context.get('install_mode', False):
            for serv in self.read(cr, uid, ids, ['name', 'host', 'port', 'dbindex', 'password'], context):
                serv_name = vals.get('name', False) and vals['name'] or serv['name']
                serv_host = vals.get('host', False) and vals['host'] or serv['host']
                serv_port = vals.get('port', False) and vals['port'] or serv['port']
                serv_dbindex = vals.get('dbindex', False) and vals['dbindex'] or serv['dbindex']
                serv_password = vals.get('password', False) and vals['password'] or serv['password']
                if redis_services.get('redis.'+serv['name'], False):
                    serv_redis = redis_services.get('redis.'+serv['name'])
                    if serv_redis.host == serv_host and serv_redis.port == serv_port and \
                        serv_redis.dbindex == serv_dbindex and serv_redis.password == serv_password:
                        pass
                    else:
                        redis_services.pop('redis.'+serv['name'])
                        serv_redis = RedisService('redis.'+serv_name, serv_host, serv_port, serv_dbindex, serv_password)
            res = osv.osv.write(self, cr, uid, ids, vals, context=context)
        return res
    
    def unlink(self, cr, uid, ids, context=None):
        for serv in self.read(cr, uid, ids, ['name'], context):
            #redis_services.get('redis.'+serv['name']).connection_pool.disconnect()
            redis_services.pop('redis.'+serv['name'])
        return osv.osv.unlink(self, cr, uid, ids, context=context)
    
    def conn(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, set, tuple)):
            ids = ids[0]
        serv = self.read(cr, uid, ids, ['name', 'host', 'port', 'dbindex', 'password'], context)
        if redis_services.get('redis.'+serv['name'], False):
            serv_redis = redis_services.get('redis.'+serv['name'])
            if not serv_redis.active:
                redis_services.pop('redis.'+serv['name'])
                serv_redis = RedisService('redis.'+serv['name'], serv['host'], serv['port'], serv['dbindex'], serv['password'])
                if not serv_redis.active:
                    return False
            if serv_redis.host == serv['host'] and serv_redis.port == serv['port'] and \
                serv_redis.dbindex == serv['dbindex'] and serv_redis.password == serv['password']:
                pass
            else:
                redis_services.pop('redis.'+serv['name'])
                serv_redis = RedisService('redis.'+serv['name'], serv['host'], serv['port'], serv['dbindex'], serv['password'])
            return serv_redis.cursor()
        else:
            serv_redis = RedisService('redis.'+serv['name'], serv['host'], serv['port'], serv['dbindex'], serv['password'])
            if not serv_redis.active:
                raise openerp.osv.osv.except_osv("Service Error", "The Service does not exist")
            else:
                return serv_redis.cursor()
    
    def ping_service(self, cr, uid, ids, context=None):
        redis_conn = self.conn(cr, uid, ids, context)
        if redis_conn:
            msg = redis_conn.ping()
        else:
            msg = "Service not connected"
        raise openerp.osv.osv.except_osv("Service Response", msg)
    
    _columns = {
        'name': fields.char('Connection Name', size=128, required=True),
        'host': fields.char('Host Name', size=128, required=True),
        'port': fields.integer('Port'),
        'dbindex': fields.integer('DB index'),
        'password': fields.char('Password', size=128),
        'value_ids': fields.one2many('solt.redis.value', 'redis_conn', string='Keys-Values'),
        'channel_ids': fields.one2many('solt.redis.channel', 'redis_conn', string='Store Channel'),
    }
    
    _defaults = {
        'port': lambda *a: 6379,
        'dbindex': lambda *a: 0,
        'password': None,
    }

solt_redis_store()

class solt_redis_value(osv.osv):
    _name = 'solt.redis.value'
    _description = 'Redis Value'
    
    def _get_real_value(self, cr, uid, ids, name, args, context):
        res = {}
        for serv in self.browse(cr, uid, ids, context):
            redis_conn = self.pool.get('solt.redis.store').conn(cr, uid, serv.redis_conn.id, context)
            if redis_conn:
                res[serv.id] = redis_conn.get(serv.name)
            else:
                res[serv.id] = ''
        return res
    
    _columns = {
        'name': fields.char('Key', size=128, required=True),
        'value': fields.text('Value'),
        'onlyread': fields.boolean('Only Read'),
        'real_value': fields.function(_get_real_value, type="text", string="Real Value"),
        #'type': fields.selection([('')],string='Type'),
        'redis_conn': fields.many2one('solt.redis.store', string="Redis Store", required=True),
    }
    
    def create(self, cr, uid, vals, context=None):
        deploy = True
        if context.get('install_mode', False):
            deploy = False
            if tools.config.get('zato_deploy', False):
                deploy = True
        if deploy:
            redis_conn = self.pool.get('solt.redis.store').conn(cr, uid, vals['redis_conn'], context)
            if redis_conn:
                redis_conn.set(vals['name'], vals['value'])
        res = osv.osv.create(self, cr, uid, vals, context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        res = True
        if not context.get('install_mode', False):
            res = osv.osv.write(self, cr, uid, ids, vals, context=context)
            for serv in self.browse(cr, uid, ids, context):
                redis_conn = self.pool.get('solt.redis.store').conn(cr, uid, serv.redis_conn.id, context)
                if redis_conn:
                    redis_conn.set(serv.name, serv.value)
        return res
    
    def unlink(self, cr, uid, ids, context=None):
        for serv in self.read(cr, uid, ids, ['name', 'redis_conn'], context):
            redis_conn = self.pool.get('solt.redis.store').conn(cr, uid, serv['redis_conn'], context)
            if redis_conn:
                redis_conn.delete(serv['name'])
            else:
                raise openerp.osv.osv.except_osv("Service Error", "The Service are not connected")
        return osv.osv.unlink(self, cr, uid, ids, context=context)
solt_redis_value()

class solt_redis_channel(osv.osv):
    _name = 'solt.redis.channel'
    _description = 'Redis Channel'
    
    _columns = {
        'name': fields.char('Channel Key', size=128, required=True),
        'subscribers': fields.one2many('solt.redis.channel.subscriber', 'channel_id', string='Subscribers'),
        'redis_conn': fields.many2one('solt.redis.store', string="Redis Store", required=True),
    }
    
solt_redis_channel()

class solt_redis_channel_subscriber(osv.osv):
    _name = 'solt.redis.channel.subscriber'
    _description = 'Redis Channel Subscriber'
    
    _columns = {
        'name': fields.char('Model Name', size=128, required=True),
        'method': fields.char('Method Name', size=128, required=True),
        'channel_id': fields.many2one('solt.redis.channel', string="Redis Channel", required=True),
    }
    
solt_redis_channel_subscriber()

#openerpweb.session_context = session_context