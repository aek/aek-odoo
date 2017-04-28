# -*- coding: utf-8 -*-

import base64
import urllib2
from urlparse import urlparse, urlunparse

import odoo
import odoo.addons.web
from odoo import api, fields, models

class Binary(odoo.http.Controller):
    @odoo.http.route('/web_linkedin/binary/url2binary', type='json', auth='user')
    def url2binary(self, url):
        """Used exclusively to load images from LinkedIn profiles, must not be used for anything else."""
        _scheme, _netloc, path, params, query, fragment = urlparse(url)
        # media.linkedin.com is the master domain for LinkedIn media (replicated to CDNs),
        # so forcing it should always work and prevents abusing this method to load arbitrary URLs
        url = urlunparse(('http', 'media.licdn.com', path, params, query, fragment))
        bfile = urllib2.urlopen(url)
        return base64.b64encode(bfile.read())
    
class web_linkedin_settings(models.TransientModel):
    _inherit = 'sale.config.settings'

    api_key = fields.Char("API Key", size=50)
    server_domain = fields.Char()

    @api.model
    def get_default_linkedin(self, fields):
        key = self.env["ir.config_parameter"].get_param("web.linkedin.apikey") or ""
        dom = self.env['ir.config_parameter'].get_param('web.base.url')
        return {'api_key': key, 'server_domain': dom,}

    @api.multi
    def set_linkedin(self):
        key = self.api_key or ""
        self.env["ir.config_parameter"].set_param("web.linkedin.apikey", key, groups=['base.group_user'])

class web_linkedin_fields(models.Model):
    _inherit = 'res.partner'

    # @api.multi
    # def _get_url(self):
    #     for partner in self.browse(cr, uid, ids, context=context):
    #         res[partner.id] = partner.linkedin_url
    #     return res

    @api.model
    def linkedin_check_similar_partner(self, linkedin_datas):
        res = []
        for linkedin_data in linkedin_datas:
            partner_ids = self.env['res.partner'].search(["|", ("linkedin_id", "=", linkedin_data['id']),
                    "&", ("linkedin_id", "=", False), 
                    "|", ("name", "ilike", linkedin_data['firstName'] + "%" + linkedin_data['lastName']), ("name", "ilike", linkedin_data['lastName'] + "%" + linkedin_data['firstName'])])
            if partner_ids:
                partner = partner_ids.read(["image", "mobile", "phone", "parent_id", "name", "email", "function", "linkedin_id"])
                if partner['linkedin_id'] and partner['linkedin_id'] != linkedin_data['id']:
                    partner.pop('id')
                if partner['parent_id']:
                    partner['parent_id'] = partner['parent_id'][0]
                for key, val in partner.items():
                    if not val:
                        partner.pop(key)
                res.append(partner)
            else:
                res.append({})
        return res


    linkedin_id = fields.Char("LinkedIn ID")
    linkedin_url = fields.Char("LinkedIn url")
    # linkedin_public_url = fields.Text(computed=_get_url, string="LinkedIn url",
    #     help="This url is set automatically when you join the partner with a LinkedIn account.")
