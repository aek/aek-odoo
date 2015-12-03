# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution
#    Copyright (C) 2010  Adrián Bernardi, Mario Puntin
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv,fields
from openerp import models
from openerp import api, fields as Fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

##mapping invoice type to journal code
TYPE2CODEJOURNAL = {
    'out_invoice': _('SAJ'),
    'in_invoice': _('EXJ'),
    'out_refund': _('SCNJ'),
    'in_refund': _('ECNJ'),
}
## Is to english journal data
# TYPE2CODEJOURNAL = {
#     'out_invoice': 'SAJ',
#     'in_invoice': 'EXJ',
#     'out_refund': 'SCNJ',
#     'in_refund': 'ECNJ',
# }


class medical_journal(osv.osv):
    _inherit = "account.journal"

    def _all_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict(map(lambda x: (x,0.0), ids))
        # The current user may not have access rights for sale orders
        try:
            for journal in self.browse(cr, uid, ids, context):
                total = 0.0
                for mo_line in self._get_account_move_line_ids(cr, uid, ids, context=context):
                    total += mo_line.commision_amount
                res[journal.id] = total
        except:
            pass
        return res
    
    def _paid_count(self, cr, uid, ids, field_name, arg, context=None):
        res = dict(map(lambda x: (x,0.0), ids))
        context = dict(context or {}, invoice_type='paid')
        # The current user may not have access rights for sale orders
        try:
            for journal in self.browse(cr, uid, ids, context):
                total = 0.0
                for mo_line in self._get_account_move_line_ids(cr, uid, ids, context=context):
                    total += mo_line.commision_amount
                res[journal.id] = total
        except:
            pass
        return res
    
    
    _columns = {
        'entry_ids': fields.one2many('account.move', 'journal_id', string='Entries', domain=[('to_check', '=', True),('inv_line', '=', False)]),
        'all_count': fields.function(_all_count, string='All', type='float', digits_compute=dp.get_precision('Product Price')),
        'paid_count': fields.function(_paid_count, string='Paid', type='float', digits_compute=dp.get_precision('Product Price')),
    }
    
    def _choose_account_from_po_line(self, cr, uid, po_line, fiscal_position, context=None):
        fiscal_obj = self.pool.get('account.fiscal.position')
        property_obj = self.pool.get('ir.property')
        if po_line.product_id:
            acc_id = po_line.product_id.property_account_expense.id
            if not acc_id:
                acc_id = po_line.product_id.categ_id.property_account_expense_categ.id
            if not acc_id:
                raise osv.except_osv(_('Error!'), _('Define an expense account for this product: "%s" (id:%d).') % (po_line.product_id.name, po_line.product_id.id,))
        else:
            acc_id = property_obj.get(cr, uid, 'property_account_expense_categ', 'product.category', context=context).id
        fpos = fiscal_position or False
        return fiscal_obj.map_account(cr, uid, fpos, acc_id)
    
    def generate_invoice(self, cr, uid, ids, move_lines=None, context=None):
        context = dict(context or {}, type = 'in_invoice')
        invoice_pool = self.pool.get('account.invoice')
        invoice_line_pool = self.pool.get('account.invoice.line')
        doctor_pool = self.pool.get('medical.physician')
        
        journal = self.browse(cr, uid, ids, context=context)[0]
        doctor_id = doctor_pool.search(cr, uid, [('journal_id', '=', journal.id)], context=context)[0]
        partner_id = doctor_pool.browse(cr, uid, doctor_id, context=context).partner_id
        line_ids = []
        move_ids = {}
        for mo_line in move_lines or self._get_account_move_line_ids(cr, uid, ids, context=context):
            account_id = self._choose_account_from_po_line(cr, uid, mo_line, partner_id.property_account_position, context=context)
            line_vals = {
                'name': mo_line.name,
                'account_id': account_id,
                'price_unit': mo_line.commision_amount,
                'quantity': mo_line.quantity,
                'product_id': mo_line.product_id.id or False,
                'uos_id': mo_line.product_uom_id.id or False,
                'invoice_line_tax_id': [(6, 0, [mo_line.account_tax_id,] and mo_line.account_tax_id or [])],
                'account_analytic_id': mo_line.analytic_account_id.id or False,
            }
            inv_line = invoice_line_pool.create(cr, uid, line_vals, context=context)
            line_ids.append(inv_line)
            if not move_ids.get(str(mo_line.move_id.id),False):
                move_ids[str(mo_line.move_id.id)] = True
                mo_line.move_id.write({'inv_line': inv_line})
        if move_ids:
            inv_name = '%s - %s'%(journal.name, fields.date.context_today(self, cr, uid, context=context))
            invoice_vals = {
                'name': inv_name,
                'reference': inv_name,
                'account_id': partner_id.property_account_payable.id,
                'type': 'in_invoice',
                'partner_id': partner_id.id,
                'currency_id': journal.currency.id or journal.company_id.currency_id.id,
                #'journal_id': len(journal_ids) and journal_ids[0] or False,
                'invoice_line': [(6, 0, line_ids)],
                'origin': journal.name,
                'fiscal_position': partner_id.property_account_position.id or False,
                'payment_term': partner_id.property_supplier_payment_term.id,
                'company_id': journal.company_id.id,
            }
            inv_id = invoice_pool.create(cr, uid, invoice_vals, context=context)
            self.pool.get('account.move').write(cr, uid, [int(key) for key in move_ids.keys()], {'to_check': False}, context=context)

            return {
                'name': _('Supplier Invoices'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.invoice',
                'view_id': False,
                'context': '{}',
                'type': 'ir.actions.act_window',
                'res_id': inv_id,
            }
        return True

    def _get_account_move_line_ids(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, [], context=context)
        result = [('type', '=', 'src'),
                  ('move_id.to_check', '=', True),
                  ('move_id.journal_id', '=', ids[0]),
                  ('move_id.inv_line', '=', False)]
        invoice_type = dict(context or {}).get('invoice_type', 'all')
        move_lines = obj.env['account.move.line'].search(result)
        if invoice_type == 'paid':
            inv = obj.env['account.invoice'].search([('move_id', 'in', list({i.move_id.id for i in move_lines})), ('state', '=', 'paid')])
            move_lines = obj.env['account.move.line'].search([('type', '=', 'src'), ('move_id', 'in', [i.move_id.id for i in inv])])
        return move_lines

medical_journal()


class medical_account_move_line(osv.osv):
    _inherit = 'account.move.line'
    
    def _get_commision(self, cr, uid, ids, field_name, args, context=None):
        res = dict(map(lambda x: (x,0.0), ids))
        move_ids = self.search(cr, uid, [('type','=','src'),('move_id.to_check', '=', True)], context=context)
        for line in self.browse(cr, uid, move_ids, context):
            res[line.id] = line.credit * line.product_id.commision / 100
        return res
    
    _columns = {
        'type': fields.char('Type', size=10),
        'commision_amount': fields.function(_get_commision, type="float", digits_compute=dp.get_precision('Product Price'), string="Sales Commision"),
    }

    def create(self, *args, **kwargs):
        return super(medical_account_move_line, self).create(*args, **kwargs)

    def write(self, *args, **kwargs):
        res = super(medical_account_move_line, self).write(*args, **kwargs)
        return res
medical_account_move_line()


class medical_account_move(osv.osv):
    _inherit = 'account.move'
    
    def _get_commision(self, cr, uid, ids, field_name, args, context=None):
        res = dict(map(lambda x: (x,0.0), ids))
        for move in self.browse(cr, uid, ids, context):
            total_commision = 0
            for line in move.line_id:
                total_commision += line.commision_amount
            res[move.id] = total_commision
        return res
    
    _columns = {
        'inv_line': fields.many2one('account.invoice.line', string='Inv Line'),
        'commision_amount': fields.function(_get_commision, type="float", digits_compute=dp.get_precision('Product Price'), string="Sales Commision"),
    }
    _defaults = {
        'to_check': True,
    }
medical_account_move()


class medical_invoice(models.Model):
    _inherit = "account.invoice"
    _order = "date_invoice desc, date_due desc"


    @api.model
    def _default_journal(self):
        inv_type = self._context.get('type', 'out_invoice')
        inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('code', 'in', filter(None, map(TYPE2CODEJOURNAL.get, inv_types))),
            ('company_id', '=', company_id),
        ]

        return self.env['account.journal'].search(domain, limit=1)



    @api.model
    def line_get_convert(self, line, part, date):
        res = super(medical_invoice, self).line_get_convert(line, part, date)
        res['type'] = line.get('type', False)
        return res

    _defaults = {

        'journal_id': _default_journal,

    }





class medical_invoice_line(models.Model):
    _inherit = "account.invoice.line"
    
    def unlink(self, cr, uid, ids, context=None):
        move_pool = self.pool.get('account.move')
        move_ids = move_pool.search(cr, uid, [('inv_line','in',ids)], context=context)
        move_pool.write(cr, uid, move_ids, {'to_check': True})
        return models.Model.unlink(self, cr, uid, ids, context=context)
    