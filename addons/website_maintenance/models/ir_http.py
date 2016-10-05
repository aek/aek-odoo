# -*- coding: utf-8 -*-

from openerp.http import request
from openerp.osv import orm

from openerp.http import request

from werkzeug.urls import url_encode, url_quote, url_join
from werkzeug.routing import RequestRedirect


class ir_http(orm.AbstractModel):
    _inherit = 'ir.http'

    def _find_handler(self, return_rule=False):
        website = request.env['website'].browse(1)
        if website.maintenance_mode:
            ir_model = request.env['ir.model.data'].sudo()
            allowed_group = ir_model.get_object('base','group_website_designer')
            group_ids = request.env['res.groups'].sudo().search([('users.id', '=', request.context.get('uid'))])
            if allowed_group.id not in group_ids.ids:
                map_adapter = self.routing_map().bind_to_environ(request.httprequest.environ)
                if request._request_type == 'http':
                    redirect_url = '/website/maintenance'
                else:
                    redirect_url = '/website/maintenance_status'
                if map_adapter.path_info not in ('/website/maintenance', '/website/maintenance_status', '/logo.png'):
                    redirect_obj = RequestRedirect(str(url_join('%s://%s%s%s' % (
                        map_adapter.url_scheme,
                        map_adapter.subdomain and map_adapter.subdomain + '.' or '',
                        map_adapter.server_name,
                        map_adapter.script_name
                    ), redirect_url)))
                    redirect_obj.code = 302
                    raise redirect_obj
        return super(ir_http, self)._find_handler(return_rule=return_rule)