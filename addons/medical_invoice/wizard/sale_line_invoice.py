# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, exceptions, fields, models, workflow
from openerp.tools.translate import _


class SaleOrderLineMakeInvoice(models.TransientModel):
    _inherit = "sale.order.line.make.invoice"

    def _get_co_payment_able(self):
        lines = self._get_sale_lines()
        sales = []
        for l in lines:
            if l.order_id.id not in sales:
                sales.append(l.order_id.id)
        return bool(self._get_insurance()) and len(sales) == 1

    def _get_order(self):
        lines = self._get_sale_lines()
        return (lines[0].order_id
                if bool(lines) and bool(lines[0].order_id)
                else self.env['sale.order'])

    def _get_patient(self):
        sale = self._get_order()
        patient = self.env['medical.patient'].search([('partner_id', '=', sale.partner_id.id)])
        if not patient:
            patient = sale.evaluation.name if bool(sale.evaluation) else False
        return patient if patient else self.env['medical.patient']

    def _get_insurance(self):
        patient = self._get_patient()
        return patient.insurances[0] if len(patient.insurances) > 1 else patient.insurances

    def _get_sale_lines(self):
        return self.env['sale.order.line'].browse(self._context.get('active_ids', False))

    co_payment_able = fields.Boolean(string='Co payment able', default=_get_co_payment_able)
    patient = fields.Many2one('medical.patient', string='Patient', default=_get_patient)
    insurance = fields.Many2one('medical.insurance', string='Insurance', default=_get_insurance)
    co_payment_method = fields.Selection([(1, 'Co payment'), (2, 'Invoice all to insurance')], 'Co payment method')
    lines = fields.One2many('sale.order.co.payment.line', 'wizard', string='Lines', required=True)

    @api.onchange('co_payment_method')
    def onchange_co_payment(self):
        lines = []
        if self.co_payment_method == 1:
            sale_lines = self._get_sale_lines()
            lines = [(0, 0, line)
                     for line in [{'order_line': line.id,
                                   'patient_amount': line.price_subtotal / 2,
                                   'insurance_amount': line.price_subtotal - (line.price_subtotal / 2)}
                                  for line in sale_lines]]
        self.lines = lines

    def _prepare_invoices(self, sale):

        def _get_invoice_dict(lines, partner):
            return {
                'name': _('Co payment of %s') % (sale.client_order_ref or sale.name),
                'origin': sale.name,
                'type': 'out_invoice',
                'reference': "P%dSO%d" % (partner.id, sale.id),
                'account_id': self.patient.partner_id.property_account_receivable.id,
                'partner_id': partner.id,
                'invoice_line': [(4, idx) for idx in lines],
                'currency_id': sale.pricelist_id.currency_id.id,
                'comment': sale.note,
                'payment_term': partner.property_payment_term.id,
                'fiscal_position': sale.fiscal_position.id or partner.property_account_position.id,
                'user_id': sale.user_id and sale.user_id.id or False,
                'company_id': sale.company_id and sale.company_id.id or False,
                'date_invoice': fields.date.today(),
                'section_id': sale.section_id.id,
            }
        line_ids = self.lines.create_invoice_lines()
        return [_get_invoice_dict([i[0] for i in line_ids], self.insurance.company),
                _get_invoice_dict([i[1] for i in line_ids], self.patient.partner_id)]

    @api.multi
    def make_invoices(self):
        sale = self._get_order()
        if not self.patient or not sale:
            return super(SaleOrderLineMakeInvoice, self).make_invoices()
        if self.lines:
            invoices = [self.env['account.invoice'].create(vals).id for vals in self._prepare_invoices(sale)]
            for invoice in invoices:
                self._cr.execute(
                    'INSERT INTO sale_order_invoice_rel (order_id,invoice_id) values (%s,%s)', (sale.id, invoice))
            sale.invalidate_cache(['invoice_ids'])
            flag = True
            sale.message_post(body=_("Invoice created"))
            for line in sale.order_line:
                if not line.invoiced and line.state != 'cancel':
                    flag = False
                    break
            if flag:
                sale.write({'state': 'progress'})
                workflow.trg_validate(self._uid, 'sale.order', sale.id, 'all_lines', self._cr)
            if self._context.get('open_invoices', False):
                return self.open_invoices(invoices)
            return {'type': 'ir.actions.act_window_close'}
        inv_ids0 = set(inv.id for inv in sale.invoice_ids)
        res = super(SaleOrderLineMakeInvoice, self).make_invoices()
        inv_ids1 = set(inv.id for inv in sale.invoice_ids)
        invoices = list(inv_ids1 - inv_ids0)
        invoice_dict = dict(
            account_id=self.patient.partner_id.property_account_receivable.id,
        )
        if self.co_payment_method == 2:
            invoice_dict.update(
                partner_id=self.insurance.company.id,
                name=_('Co payment of %s') % (sale.client_order_ref or sale.name),
            )
        else:
            invoice_dict.update(partner_id=self.patient.partner_id.id)
        self.env['account.invoice'].browse(invoices).write(invoice_dict)
        return res

    @api.multi
    def open_invoices(self, invoice_ids):
        invoice_ids = [invoice_ids] if isinstance(invoice_ids, int) else invoice_ids
        res = super(SaleOrderLineMakeInvoice, self).open_invoices(invoice_ids[0])
        if len(invoice_ids) <= 1:
            return res
        views = res.get('views', [])
        views.reverse()
        res.update(
            view_mode='tree, form',
            domain=[('id', 'in', invoice_ids)],
            res_id=False,
            views=views
        )
        return res


class SaleOrderCoPaymentLine(models.TransientModel):
    _name = 'sale.order.co.payment.line'

    @api.one
    @api.depends('patient_amount')
    def _compute_insurance_amount(self):
        self.insurance_amount = self.order_line.price_subtotal - self.patient_amount

    wizard = fields.Many2one('sale.order.line.make.invoice')
    order_line = fields.Many2one('sale.order.line', required=True)
    patient_amount = fields.Float()
    insurance_amount = fields.Float(compute="_compute_insurance_amount")

    @api.one
    @api.constrains('patient_amount')
    def _check_amounts(self):
        if self.patient_amount <= 0.0 or self.insurance_amount <= 0.0:
            raise exceptions.ValidationError(
                _('Patient and Insurance amounts should be positives.'))

    def _prepare_invoice_lines(self, insurance=False):
        ir_property_obj = self.env['ir.property']
        sale = self.order_line.order_id
        prop = ir_property_obj.get('property_account_income_categ', 'product.category')
        account_id = sale.fiscal_position.map_account(prop.id if prop else False)
        if not account_id:
            raise exceptions.ValidationError(_('There is no income account defined as global property.'))
        inv_amount = self.insurance_amount if insurance else self.patient_amount
        if inv_amount <= 0.00:
            raise exceptions.ValidationError(_('The value of Advance Amount must be positive.'))
        symbol = sale.pricelist_id.currency_id.symbol
        if sale.pricelist_id.currency_id.position == 'after':
            symbol_order = (inv_amount, symbol, self.order_line.name)
        else:
            symbol_order = (symbol, inv_amount, self.order_line.name)
        name = _("Co payment for %s %s of: %s") % symbol_order
        return {
            'name': name,
            'origin': sale.name,
            'account_id': account_id,
            'product_id': self.order_line.product_id.id,
            'price_unit': inv_amount,
            'invoice_line_tax_id': [(6, 0, self.order_line.tax_id.ids)] if self.order_line.tax_id and not insurance else [],
            'account_analytic_id': sale.project_id.id or False,
        }

    @api.one
    @api.multi
    def create_invoice_lines(self):
        if not ((not self.order_line.invoiced) and (self.order_line.state not in ('draft', 'cancel'))):
            raise exceptions.ValidationError(
                _('Invoice cannot be created for this Sales Order Line due to one of the following reasons:\n'
                  '1.The state of this sales order line is either "draft" or "cancel"!\n'
                  '2.The Sales Order Line is Invoiced!'))
        inv_line = self.env['account.invoice.line']
        res = inv_line.create(self._prepare_invoice_lines()).id, inv_line.create(self._prepare_invoice_lines(True)).id
        self.order_line.write({'invoice_lines': [(4, idx) for idx in res], 'invoiced': True})
        return res




