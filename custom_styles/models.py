import base64
from odoo import fields, models, api


class custom_styles(models.Model):
    _name = 'custom.styles'

    name = fields.Char(required=True)
    data = fields.Text(required=True)
    mimetype = fields.Selection([('text/css', 'CSS'), ('text/less', 'LESS'), ('text/javascript', 'JavaScript')], string='Type', required=True, default='text/css')
    active = fields.Boolean(default=True)
    attachment_id = fields.Many2one('ir.attachment')
    view_id = fields.Many2one('ir.ui.view')

    @api.model
    def create(self, vals):
        res = super(custom_styles, self).create(vals)
        res.confirm()
        return res

    @api.multi
    def write(self, vals):
        super(custom_styles, self).write(vals)
        self.confirm()
        return True

    @api.multi
    def confirm(self):
        attach_data = {
            'name': self.name,
            'type': "binary",
            'mimetype': self.mimetype,
            'public': True,
            'datas': base64.encodestring(self.data.encode('utf-8')),
            'datas_fname': self.name,
        }

        if self.attachment_id:
            # If it was already modified, simply override the corresponding attachment content
            attach_data['url'] = '/web/content/%d' % self.attachment_id.id
            self.attachment_id.write(attach_data)
        else:
            # If not, create a new attachment to copy the original LESS file content, with its modifications
            self.attachment_id = self.env["ir.attachment"].create(attach_data)
            self.attachment_id.write({'url': '/web/content/%d' % self.attachment_id.id})

        if self.mimetype == 'text/javascript':
            asset_def = """<script type="%(mimetype)s" src="%(new_url)s"></script>""" % {
                'new_url': '/web/content/%d' % self.attachment_id.id,
                'mimetype': self.mimetype
            }
        else:
            asset_def = """<link type="%(mimetype)s" rel="stylesheet" href="%(new_url)s"/>""" % {
                'new_url': '/web/content/%d' % self.attachment_id.id,
                'mimetype': self.mimetype
            }

        view_data = {
            'name': self.name,
            'mode': "extension",
            'inherit_id': self.env.ref('website.assets_frontend').id,
            'active': self.active,
            'arch': """
                <data inherit_id="%(inherit_xml_id)s" name="%(name)s">
                    <xpath expr="." position="inside">
                        %(asset_def)s
                    </xpath>
                </data>
            """ % {
                'inherit_xml_id': 'website.assets_frontend',
                'name': self.name,
                'asset_def': asset_def
            }
        }
        if self.view_id:
            self.view_id.write(view_data)
        else:
            self.view_id = self.env["ir.ui.view"].create(view_data)

        # self.write({'attachment_id': self.attachment_id.id, 'view_id': self.view_id.id})
        self.env["ir.qweb"].clear_caches()

    @api.multi
    def unlink(self):
        self.view_id.unlink()
        self.attachment_id.unlink()
        self.env["ir.qweb"].clear_caches()
        return super(custom_styles, self).unlink()
