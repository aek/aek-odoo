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
from openerp import api, exceptions, fields, models, _


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _get_co_payment_able(self):
        sales = self.env['sale.order'].browse(self._context.get('active_ids', False))
        return bool(self._get_insurance()) and len(sales) == 1

    def _get_order(self):
        sales = self.env['sale.order'].browse(self._context.get('active_ids', False))
        return sales[0] if len(sales) > 1 else sales

    def _get_patient(self):
        sale = self._get_order()
        patient = self.env['medical.patient'].search([('partner_id', '=', sale.partner_id.id)])
        if not patient:
            patient = sale.evaluation.name if bool(sale.evaluation) else False
        return patient if patient else self.env['medical.patient'] 

    def _get_insurance(self):
        patient = self._get_patient()
        return patient.insurances[0] if len(patient.insurances) > 1 else patient.insurances

    @api.one
    @api.depends('patient_amount')
    def _compute_insurance_amount(self):
        sale = self._get_order()
        self.insurance_amount = sale.amount_total - self.patient_amount

    co_payment_able = fields.Boolean(string='Co payment able', default=_get_co_payment_able)
    patient = fields.Many2one('medical.patient', string='Patient', default=_get_patient)
    insurance = fields.Many2one('medical.insurance',string='Insurance', default=_get_insurance)
    co_payment_method = fields.Selection([(1, 'Co payment'), (2, 'Invoice all to insurance')], 'Co payment method')
    patient_amount = fields.Float('Patient amount')
    insurance_amount = fields.Float('Insurance amount',compute="_compute_insurance_amount")

    @api.one
    @api.constrains('patient_amount')
    def _check_amounts(self):
        if self.co_payment_able and self.co_payment_method == 1 and (self.patient_amount <= 0.0 or self.insurance_amount <= 0.0):
            raise exceptions.ValidationError(
                _('Patient and Insurance amounts should be positives.'))

    @api.onchange('advance_payment_method', 'product_id', 'co_payment_method')
    def onchange_method(self):
        if self.advance_payment_method == 'percentage':
            self.amount = 0
            self.product_id = self.env['product.product']
        elif self.product_id:
            self.amount = self.product_id.list_price
        else:
            self.amount = 0
        if (self.advance_payment_method in ('fixed', 'percentage') and self.co_payment_method == 1) or self.advance_payment_method == 'lines':
            self.co_payment_method = False

    def _prepare_invoice_vals(self):
        sale = self._get_order()
        invoice_line = self.env['account.invoice.line']
        ir_property_obj = self.env['ir.property']
        doctor_pool = self.env['medical.physician']
        
        prop = ir_property_obj.get('property_account_income_categ', 'product.category')
        account_id = sale.fiscal_position.map_account(prop.id if prop else False)
        if not account_id:
            raise exceptions.ValidationError(
                _('There is no income account defined as global property.'))
        vals = dict(account_id=account_id)
        doctor_id = doctor_pool.search([('partner_id.user_id.id', '=', sale.user_id.id),('journal_id','!=',False)])
        if doctor_id:
            vals['journal_id'] = doctor_id.journal_id.id

        def _get_specific_vals(vals, insurance=False):
            partner = self.insurance.company if insurance else self.patient.partner_id
            res = invoice_line.product_id_change(self.product_id.id, False, partner_id=partner.id,
                                                 fposition_id=sale.fiscal_position.id)['value']
            res['partner_id'] = partner.id
            res['payment_term'] = partner.property_payment_term.id
            res['price_unit'] = inv_amount = self.insurance_amount if insurance else self.patient_amount
            if not res.get('name'):
                symbol = sale.pricelist_id.currency_id.symbol
                if sale.pricelist_id.currency_id.position == 'after':
                    symbol_order = (inv_amount, symbol)
                else:
                    symbol_order = (symbol, inv_amount)
                res['name'] = _("Co payment for %s %s") % symbol_order
            if res.get('invoice_line_tax_id') and not insurance:
                res['invoice_line_tax_id'] = [(6, 0, res.get('invoice_line_tax_id'))]
            else:
                res['invoice_line_tax_id'] = False
            res.update(vals)
            return res

        def _get_vals(vals):
            inv_line_values = {
                'name': vals.get('name'),
                'origin': sale.name,
                'type': 'out_invoice',
                'account_id': vals['account_id'],
                'price_unit': vals['price_unit'],
                'quantity': 1.0,
                'discount': False,
                'uos_id': vals.get('uos_id', False),
                'product_id': self.product_id.id,
                'invoice_line_tax_id': vals.get('invoice_line_tax_id'),
                'account_analytic_id': sale.project_id.id or False,
            }
            inv_values = {
                'name': _('Co payment of %s') % (sale.client_order_ref or sale.name),
                'origin': sale.name,
                'type': 'out_invoice',
                'reference': False,
                'account_id': self.patient.partner_id.property_account_receivable.id,
                'partner_id': vals['partner_id'],
                'invoice_line': [(0, 0, inv_line_values)],
                'currency_id': sale.pricelist_id.currency_id.id,
                'comment': sale.note,
                'payment_term': vals['payment_term'],
                'fiscal_position': sale.fiscal_position.id or sale.partner_id.property_account_position.id,
                'user_id': sale.user_id and sale.user_id.id or False,
                'company_id': sale.company_id and sale.company_id.id or False,
                'date_invoice': fields.date.today(),
                'section_id': sale.section_id.id,
            }
            if vals.get('journal_id', False):
                inv_values['journal_id'] = vals['journal_id']
            return inv_values
        
        return [(sale.id, _get_vals(_get_specific_vals(vals))), (sale.id, _get_vals(_get_specific_vals(vals, True)))]

    @api.multi
    def create_invoices(self):
        if not self.co_payment_able or self.co_payment_method not in (1, 2):
            return super(SaleAdvancePaymentInv, self).create_invoices()
        sale = self._get_order()
        if self.co_payment_method == 2:
            inv_ids0 = set(inv.id for inv in sale.invoice_ids)
            super(SaleAdvancePaymentInv, self).create_invoices()
            inv_ids1 = set(inv.id for inv in sale.invoice_ids)
            invoices = list(inv_ids1 - inv_ids0)
            invoice_dict = dict(
                account_id=self.patient.partner_id.property_account_receivable.id,
                partner_id=self.insurance.company.id,
                name=_('Co payment of %s') % (sale.client_order_ref or sale.name),
            )
            self.env['account.invoice'].browse(invoices).write(invoice_dict)
        elif self.advance_payment_method == 'all':
            invoices = []
            for sale_id, inv_values in self._prepare_invoice_vals():
                invoices.append(self._create_invoices(inv_values, sale_id))
            sale.write({'state': 'progress'})

        if self._context.get('open_invoices', False):
            return self.open_invoices(invoices)
        return {'type': 'ir.actions.act_window_close'}


    @api.multi
    def open_invoices(self, invoice_ids):
        res = super(SaleAdvancePaymentInv, self).open_invoices(invoice_ids)
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
