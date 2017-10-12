# -*- coding: utf-8 -*-

import json
import requests
import logging

try:
    import urlparse
except ImportError:
    from urllib import parse as urlparse

from odoo import api, models, fields, _, exceptions

_logger = logging.getLogger(__name__)


class mailchimp_campaign(models.Model):
    _inherit = 'mail.mass_mailing'
    
    chimp_id = fields.Char('MailChimp ID')
    chimp_data = fields.Text('MailChimp Data')
    chimp_member_ids = fields.One2many('mailchimp.list.member', 'mailing_id', 'Members')

    @api.multi
    def export_list(self):
        company_id = self.env.user.company_id
        apikey = self.env['ir.config_parameter'].get_param('mailchimp.apikey', default=False)
        if apikey:
            parts = apikey.split('-')
            if len(parts) == 2:
                shard = parts[1]
            for campaign in self:
                
                if campaign.chimp_id:
                    method = 'patch'
                    api_root = "https://%s.api.mailchimp.com/3.0/lists/%s" % (shard, campaign.chimp_id)
                else:
                    method = 'post'
                    api_root = "https://%s.api.mailchimp.com/3.0/lists/" % shard
                data = {
                    "name": campaign.name,
                    "contact": {
                        "company": company_id.name,
                        "address1": company_id.street or '',
                        "city": company_id.city or '',
                        "state": company_id.state_id.name or '',
                        "zip": company_id.zip or '',
                        "country": company_id.country_id.name or ''
                    },
                    "campaign_defaults": {
                        "from_name": company_id.name,
                        "from_email": campaign.email_from,
                        "subject": campaign.name,
                        "language": "Spanish"
                    },
                    "visibility": "prv",
                    "permission_reminder": company_id.email,
                    "email_type_option": False
                }
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': 'apikey %s' % apikey
                }
                
                response = getattr(requests, method)(api_root, data=json.dumps(data), auth=None, headers=headers)
                resp = json.loads(response.text)
                campaign.write({'chimp_id': resp.get('id'), 'chimp_data': response.text})
                if resp.get('status') == 400:
                    raise exceptions.ValidationError(resp.get('detail')+"\n"+"\n".join([
                        error.get('message') for error in resp.get('errors')
                    ]))
                mem_ids = campaign.get_recipients()

                model_pool = self.env[campaign.mailing_model]
                for elem in model_pool.browse(mem_ids):
                    email = ''
                    if 'email' in model_pool._fields:
                        email = elem.email
                    elif 'email_from' in model_pool._fields:
                        email = elem.email_from
                    elif 'partner_id' in model_pool._fields:
                        email = elem.partner_id.email
                    if email:
                        exist_ids = self.env['mailchimp.list.member'].search([
                            ('mailing_model', '=',campaign.mailing_model),
                            ('res_id', '=', elem.id),
                            ('mailing_id', '=', campaign.id)
                        ])
                        if not exist_ids:
                            self.env['mailchimp.list.member'].create({
                                'name': email,
                                'mailing_model': campaign.mailing_model,
                                'res_id': elem.id,
                                'mailing_id': campaign.id
                            })
                        else:
                            exist_ids.write({'name': email})

            self.export_list_member()

    @api.multi
    def export_list_member(self):
        apikey = self.env['ir.config_parameter'].get_param('mailchimp.apikey', False)
        if apikey:
            parts = apikey.split('-')
            if len(parts) == 2:
                shard = parts[1]
                
            for campaign in self:
                for member in campaign.chimp_member_ids:
                    if member.chimp_id:
                        method = 'patch'
                        api_root = "https://%s.api.mailchimp.com/3.0/lists/%s/members/%s/" % (
                            shard, campaign.chimp_id, member.chimp_id
                        )
                    else:
                        method = 'post'
                        api_root = "https://%s.api.mailchimp.com/3.0/lists/%s/members/" % (shard, campaign.chimp_id)
                    
                    data = {
                        'email_address': member.name,
                        'status': 'subscribed',#['pending', 'subscribed', 'unsubscribed', 'cleaned']
                        #'merge_fields': {
                        #    'FNAME': 'Axel',
                        #    'LNAME': 'Mendoza',
                        #}
                    }
                    headers = {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'Authorization': 'apikey %s' % apikey
                    }
                    response = getattr(requests, method)(api_root, data=json.dumps(data), auth=None, headers=headers)
                    resp = json.loads(response.text)
                    if resp.get('status') == 400:
                        raise exceptions.ValidationError('Member: %s'%member.name + '\n'+resp.get('detail'))

                    member.write({'chimp_id': resp.get('id'), 'chimp_data': response.text})


class mailchimp_list_member(models.Model):
    _name = 'mailchimp.list.member'
    
    name = fields.Char('Email')
    mailing_model = fields.Char('Mailing Model')
    res_id = fields.Integer('Resource Id')
    mailing_id = fields.Many2one('mail.mass_mailing', 'Mass Mailing')
    chimp_id = fields.Char('MailChimp ID')
    chimp_data = fields.Text('MailChimp Data')


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    _mail_mass_mailing = _('Employees')


class res_partner(models.Model):
    _inherit = 'res.partner'

    _mail_mass_mailing = _('Students')
