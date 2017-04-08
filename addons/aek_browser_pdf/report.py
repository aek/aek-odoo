# -*- coding: utf-8 -*-
import os
import lxml.html

from openerp import api, fields, models
from functools import partial

class Report(models.Model):
    _inherit = "report"

    @api.multi
    def get_action_html(self, report_name, data=None):
        qwebtypes = ['qweb-pdf', 'qweb-html']
        conditions = [('report_type', 'in', qwebtypes), ('report_name', '=', report_name)]
        report = self.env['ir.actions.report.xml'].search(conditions)[0]
        user = self.env.user

        if not report.paperformat_id:
            paperformat = user.company_id.paperformat_id
        else:
            paperformat = report.paperformat_id

        html = self.get_html(self, report_name, data=data)
        html = html.decode('utf-8')  # Ensure the current document is utf-8 encoded.
        root = lxml.html.fromstring(html)
        match_klass = "//div[contains(concat(' ', normalize-space(@class), ' '), ' {} ')]"

        css = ''  # Will contain local css
        headerhtml = []
        contenthtml = []
        footerhtml = []
        base_url = self.env['ir.config_parameter'].sudo().get_param('report.url') or self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        for node in root.xpath("//html/head/style"):
            css += node.text

        for node in root.xpath(match_klass.format('header')):
            body = lxml.html.tostring(node)
            header = self.pool['ir.ui.view'].render(self._cr, self._uid, 'report.minimal_layout', values=dict(css=css, subst=False, body=body, base_url=base_url), context=self._context)
            headerhtml.append(header)

        for node in root.xpath(match_klass.format('footer')):
            body = lxml.html.tostring(node)
            footer = self.pool['ir.ui.view'].render(self._cr, self._uid, 'report.minimal_layout', values=dict(css=css, subst=False, body=body, base_url=base_url), context=self._context)
            footerhtml.append(footer)

        for node in root.xpath(match_klass.format('page')):
            body = lxml.html.tostring(node)
            reportcontent = self.pool['ir.ui.view'].render(self._cr, self._uid, 'report.minimal_layout', values=dict(css=css, subst=False, body=body, base_url=base_url), context=self._context)
            contenthtml.append(reportcontent)

        return {
            'headers': "".join(headerhtml),
            'content': html,
            'footers': "".join(footerhtml),
            'paper_format': self.get_paper_format(paperformat)
        }

    def get_paper_format(self, paperformat):
        res = {}
        if paperformat.format and paperformat.format != 'custom':
            res['page_size'] = paperformat.format

        if paperformat.page_height and paperformat.page_width and paperformat.format == 'custom':
            res['page_width'] = paperformat.page_width
            res['page_height'] = paperformat.page_height

        res['margin-top'] = paperformat.margin_top

        if paperformat.dpi:
            if os.name == 'nt' and int(paperformat.dpi) <= 95:
                res['dpi'] = '96'
            else:
                res['dpi'] = paperformat.dpi

        if paperformat.header_spacing:
            res['header-spacing'] = paperformat.header_spacing

        res['margin-left'] = paperformat.margin_left
        res['margin-bottom'] = paperformat.margin_bottom
        res['margin-right'] = paperformat.margin_right
        if paperformat.orientation:
            res['orientation'] = paperformat.orientation
        if paperformat.header_line:
            res['header-line'] = True

        return res
