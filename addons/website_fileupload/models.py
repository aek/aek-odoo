import odoo
from odoo import fields, models, api

class website_fileupload(models.Model):
    _name = 'website.custom.file.upload'

    name = fields.Char()
    file = fields.Binary('File')
