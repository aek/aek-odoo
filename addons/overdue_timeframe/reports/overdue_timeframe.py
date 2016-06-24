# -*- encoding: utf-8 -*-

import time

from openerp import fields, models, _
from openerp import tools
from openerp.report import report_sxw

import datetime

class overdue_timeframe_parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(overdue_timeframe_parser, self).__init__(cr, uid, name, context=context)
        ids = context.get('active_ids')
        partner_obj = self.pool.get('res.partner')
        docs = partner_obj.browse(cr, uid, ids, context)

        timeframe_obj = self.pool.get('overdue.timeframe')
        timeframes = timeframe_obj.browse(self.cr, self.uid, timeframe_obj.search(self.cr, self.uid, []))

        addresses = self.pool['res.partner']._address_display(cr, uid, ids, None, None)
        self.timeframe_subtotals = {}
        self.timeframes = timeframes
        invoices = self.pool.get('account.invoice').browse(self.cr, self.uid, self.pool.get('account.invoice').search(self.cr, self.uid, [('partner_id', 'in', ids),('state', '=', 'open')]))

        self.localcontext.update({
            'docs': docs,
            'time': time,
            'tel_get': self._tel_get,
            'addresses': addresses,
            'invoices': invoices,
            'timeframe_headers': [(frame.name, frame.color) for frame in timeframes],
            'invoice_timeframes': self._get_invoice_timeframes,
            'timeframe_subtotals': self.timeframe_subtotals,
            'invoices_total': sum([inv.residual for inv in invoices])

        })
        self.context = context

    def _get_invoice_timeframes(self, invoice):
        date_due = False
        if invoice.date_due:
            date_due = datetime.datetime.strptime(invoice.date_due, tools.DEFAULT_SERVER_DATE_FORMAT)
        res_lines = []
        current_date = datetime.datetime.strptime(fields.Date.context_today(invoice),tools.DEFAULT_SERVER_DATE_FORMAT)
        for frame in self.timeframes:
            frame_value = 0.0
            if invoice.date_invoice:
                date_invoice = datetime.datetime.strptime(invoice.date_invoice, tools.DEFAULT_SERVER_DATE_FORMAT)
                date_diff = current_date - date_invoice
                if frame.until_day:
                    if frame.before_day <= date_diff.days <= frame.until_day:
                        frame_value = invoice.residual
                elif frame.before_day < date_diff.days:
                    frame_value = invoice.residual
            frame_color = False
            if date_due and frame.color and date_due < current_date:
                frame_color = frame.color
            res_lines.append((frame_value, frame_color))
            if not self.timeframe_subtotals.get(frame.name, False):
                self.timeframe_subtotals[frame.name] = 0.0
            self.timeframe_subtotals[frame.name] += frame_value
        return res_lines

    def _tel_get(self, partner):
        if not partner:
            return False
        res_partner = self.pool['res.partner']
        addresses = res_partner.address_get(self.cr, self.uid, [partner.id], ['invoice'])
        adr_id = addresses and addresses['invoice'] or False
        if adr_id:
            adr = res_partner.read(self.cr, self.uid, [adr_id])[0]
            return adr['phone']
        else:
            return partner.phone or False
        return False


class report_overdue_timeframe(models.AbstractModel):
    _name = "report.overdue_timeframe.report_overdue_timeframe"
    _inherit = "report.abstract_report"
    _template = "overdue_timeframe.report_overdue_timeframe"
    _wrapped_report_class = overdue_timeframe_parser

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
