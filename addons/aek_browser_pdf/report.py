# -*- coding: utf-8 -*-
import os
import lxml.html

from openerp import api, fields, models
from functools import partial

class Report(models.Model):
    _inherit = "report"

    @api.model
    def get_action_html(self, docids, report_name, data=None):
        qwebtypes = ['qweb-pdf', 'qweb-html']
        conditions = [('report_type', 'in', qwebtypes), ('report_name', '=', report_name)]
        report = self.env['ir.actions.report.xml'].search(conditions)[0]

        if not report.paperformat_id:
            paperformat = self.env.user.company_id.paperformat_id
        else:
            paperformat = report.paperformat_id

        html = self.with_context(debug=False, paperformat=self.get_paper_format(paperformat)).get_html(docids, report_name, data=data)
        html = html.decode('utf-8')  # Ensure the current document is utf-8 encoded.

        return {
            'content': html,
        }

    def get_paper_format(self, paperformat):
        res = {}
        if paperformat.format and paperformat.format != 'custom':
            res['page-size'] = paperformat.format

        if paperformat.page_height and paperformat.page_width and paperformat.format == 'custom':
            res['page-size'] = '%smm %smm' %(paperformat.page_width, paperformat.page_height)

        res['margin-top'] = paperformat.margin_top
        res['margin-left'] = paperformat.margin_left
        res['margin-bottom'] = paperformat.margin_bottom
        res['margin-right'] = paperformat.margin_right
        res['dpi'] = paperformat.dpi
        res['header-spacing'] = paperformat.header_spacing
        res['orientation'] = paperformat.orientation or ''
        res['header-line'] = paperformat.header_line

        return res

class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    @api.multi
    def render(self, values=None, engine='ir.qweb'):
        if not values:
            values = {}
        if engine == 'ir.qweb':
            values['paperformat'] = self.env.context.get('paperformat', False)
        return super(IrUiView, self).render(values=values, engine=engine)


class sale_order(models.Model):
    _inherit = 'sale.order'

    # @api.multi
    # def test_action_browser_pdf(self):
        # datas = {'ids': self.ids}
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'aek_browser_pdf',
        #     'report_name': 'sale.report_saleorder',
        #     'datas': datas,
        #     'context': self.env.context
        # }

    @api.multi
    def test_action_browser_pdf(self):
        datas = {'ids': self.ids}
        return {
            'type': 'ir.actions.report.xml',
            'report_type': 'controller',
            'report_name': 'test',
            'report_file': '/web/content/ir.attachment/444/datas/visa_unidad_familiar.docx?download=true',
            'display_name': 'test',
        }