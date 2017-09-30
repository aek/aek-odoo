# -*- encoding: utf-8 -*-
from openerp import models, fields

class website(models.Model):
    _inherit = "website"
    _description = "Website"

    facebook_pixel_key = fields.Char('Facebook Pixel Key')

class website_config_settings(models.TransientModel):
    _inherit = 'website.config.settings'

    facebook_pixel_key = fields.Char(related='website_id.facebook_pixel_key', string='Facebook Pixel Key')