from openerp import models, fields, api


class website_maintenance_website(models.Model):
    _inherit = 'website'

    maintenance_mode = fields.Boolean('Enable Maintenance Mode')
    maintenance_message = fields.Char('Custom Maintenance Message')

class website_maintenance_config_settings(models.TransientModel):
    _inherit = 'website.config.settings'

    maintenance_mode = fields.Boolean(related='website_id.maintenance_mode', string='Enable Maintenance Mode')
    maintenance_message = fields.Char(related='website_id.maintenance_message', string='Custom Maintenance Message')


