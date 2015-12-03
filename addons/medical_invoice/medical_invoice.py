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
from openerp import api

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

import datetime
import time


class medical_patient(osv.osv):
    _name = "medical.patient"
    _inherit = "medical.patient"

    _columns = {
        'receivable': fields.related('partner_id', 'credit', type='float', string='Receivable', help='Total amount this patient owes you', readonly=True),
    }


medical_patient()


# Add Invoicing information to the Appointment

class medical_appointment(osv.osv):
    _name = "medical.appointment"
    _inherit = "medical.appointment"

    _columns = {
        'no_invoice': fields.boolean('Invoice exempt'),
        'public': fields.related('institution', 'is_public', type='boolean', readonly=True),
        'sale_id': fields.many2one('sale.order', string='Sale Order'),
    }

    _defaults = {
        'no_invoice': False
    }
    def onchange_doctor(self, cr, uid, ids, doctor, context):
        values = {}
        if doctor:
            doctor_id = self.pool.get('medical.physician').browse(cr, uid, doctor)
            values = super(medical_appointment, self).onchange_doctor(cr, uid, ids, doctor, context=context)
            values['value'].update({'consultations': doctor_id.spec_consultations.id})
        return values

    #===========================================================================
    # def _check_date(self, cr, uid, ids, context=None):
    #     for app in self.browse(cr, uid, ids, context=context):
    #         if app.appointment_validity_date:
    #             if app.appointment_validity_date <= app.appointment_date:
    #                 return False
    #     return True
    #===========================================================================

    _constraints = [
        #(_check_date,'The Validity Date most be posterior of Appointment date.',['appointment_date', 'appointment_validity_date']),
    ]

    @api.one
    @api.multi
    def make_sale_order(self):
        if self.no_invoice:
            return
        pricelist_id = self.doctor.pricelist_ids[0] if self.doctor.pricelist_ids else False
        vals = {
            'name': self.name,
            'date_order': self.appointment_date,
            'partner_id': self.patient.partner_id.id,
            'user_id': self.doctor.partner_id.user_id.id,
            'order_line': [[0, 0, {
                'name': self.consultations.name,
                'price_unit': self.consultations.list_price,
                'product_id': self.consultations.id,
            }]],
            'appointment': self.id
        }
        if not self.doctor.journal_id.id:
            sale_journal = self.env['account.journal'].search([('code', '=', _('SAJ'))])
            if sale_journal:
                doctor = self.doctor
                code = self.env['ir.sequence'].next_by_code('medical.journal')
                doctor_journal = sale_journal[0].copy(default={'name': doctor.name, 'code': code})
                doctor.journal_id = doctor_journal
        if pricelist_id:
            vals['pricelist_id'] = pricelist_id.id
            vals['currency_id'] = pricelist_id.currency_id.id
            vals['doctor_pricelist_ids'] = [[6, 0, [item.id for item in self.doctor.pricelist_ids]]]
        self.sale_id = self.env['sale.order'].create(vals)

    def write(self, cr, uid, ids, values, context=None):
        if values.get('state', '') == 'open':
            self.make_sale_order(cr, uid, ids, context=context)
        res = super(medical_appointment, self).write(cr, uid, ids, values, context=context)
        return res

    @api.multi
    def open_sale_order(self):
        if self.sale_id:
            return self.sale_id.get_access_action()[0]
        return True

medical_appointment()

# Add Invoicing information to the Lab Test

class medical_patient_lab_order(osv.osv):
    _name = "medical.patient.lab.order"
    _inherit = "medical.patient.lab.order"

    _columns = {
        'no_invoice': fields.boolean('Invoice exempt'),
    }
    
    _defaults = {
        'no_invoice': False
    }


medical_patient_lab_order()


class medical_patient_prescription_order(osv.osv):
    _name = "medical.prescription.order"
    _inherit = "medical.prescription.order"

    _columns = {
        'no_invoice': fields.boolean('Invoice exempt'),
    }

    _defaults = {
        'no_invoice': False
    }

medical_patient_prescription_order()


class medical_pricelist(osv.osv):
    _name = "product.pricelist"
    _inherit = 'product.pricelist'

    _columns = {
        'doctor_id': fields.many2one('medical.physician', string='Doctor'),
    }

    def _name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100, name_get_uid=None):
        if context and context.get('search_doctor_pricelists', False):
            search_doctor_pricelists = context.get('search_doctor_pricelists')
            if search_doctor_pricelists:
                args.append(('id', 'in', search_doctor_pricelists))
        return super(medical_pricelist, self)._name_search(cr, user, name, args, operator, context, limit, name_get_uid)

medical_pricelist()


class medical_sale_pricelist(osv.osv):
    _name = "sale.order"
    _inherit = "sale.order"

    _columns = {
        'doctor_pricelist_ids': fields.many2many('product.pricelist', 'sale_order_doctor_pricelist_rel', 'sale_id','pricelist_id', string='Doctor Pricelists'),
    }
    
    def calc_line(self, cr, uid, line, pricelist, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        line_pool = self.pool.get('sale.order.line')
        line_id = line_pool.browse(cr, uid, line, context=context)
        results = line_pool.product_id_change(cr, uid, line, pricelist.id, line_id.product_id.id,
                                              qty=line_id.product_uom_qty,
                                              uom=line_id.product_uom.id,
                                              qty_uos=line_id.product_uos_qty,
                                              uos=line_id.product_uos.id, name=line_id.name,
                                              fiscal_position=line_id.order_id.fiscal_position.id if line_id.order_id.fiscal_position else False,
                                              partner_id=line_id.order_id.partner_id.id,
                                              date_order=line_id.order_id.date_order, flag=False,
                                              context=context
        )
        if results.get('warning', False):
            return {'warning': results.get('warning')}
        price_unit = results['value']['price_unit']
        price = price_unit * (1 - (line_id.discount or 0.0) / 100.0)
        cur = pricelist.currency_id
        val_taxes = 0.0
        taxes = tax_obj.compute_all(cr, uid, line_id.tax_id, price, line_id.product_uom_qty, line_id.product_id.id, line_id.order_id.partner_id.id)
        for c in taxes['taxes']:
            val_taxes += c.get('amount', 0.0)
        price_subtotal = cur_obj.round(cr, uid, cur, taxes['total'])
        return {'price_subtotal': price_subtotal, 'val_taxes': val_taxes, 'price_unit': price_unit}
        
    def onchange_pricelist_id(self, cr, uid, ids, pricelist_id, order_lines, context=None):
        cur_obj = self.pool.get('res.currency')
        
        context = context or {}
        if not pricelist_id:
            return {}
        pricelist = self.pool.get('product.pricelist').browse(cr, uid, pricelist_id, context=context)
        cur = pricelist.currency_id
        value = {
            'currency_id': pricelist.currency_id.id
        }
        if not order_lines or order_lines == [(6, 0, [])]:
            return {'value': value}
        else:
            
            line_vals = []
            val = val1 = 0.0
            
            for elem in order_lines:
                if elem[0] == 6:
                    for line in elem[2]:
                        res_line = self.calc_line(cr, uid, line, pricelist, context=context)
                        if res_line.get('warning', False):
                            return res_line
                        val1 += res_line['price_subtotal']
                        val += res_line['val_taxes']
                        line_vals.append((1, line, {'price_subtotal': res_line['price_subtotal'], 'price_unit': res_line['price_unit']}))
                elif elem[0] == 1:
                    line = elem[1]
                    res_vals = elem[2]
                    res_line = self.calc_line(cr, uid, line, pricelist, context=context)
                    val1 += res_line['price_subtotal']
                    val += res_line['val_taxes']
                    res_vals['price_subtotal': res_line['price_subtotal'], 'price_unit': res_line['price_unit']]
                    line_vals.append((1, line, res_vals))
                else:
                    line_vals.append(elem)
            value['order_line'] = line_vals
            value['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            value['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            value['amount_total'] = value['amount_tax'] + value['amount_untaxed']

        # =======================================================================
        # warning = {
        #     'title': _('Pricelist Warning!'),
        #     'message' : _('If you change the pricelist of this order (and eventually the currency), prices of existing order lines will not be updated.')
        # }
        #=======================================================================
        return {'value': value}

    def action_done(self, cr, uid, ids, context=None):
        super(medical_sale_pricelist, self).action_done(cr, uid, ids, context=context)
        appointment_pool = self.pool.get('medical.appointment')
        appointment_ids = appointment_pool.search(cr, uid, [('sale_id', 'in', ids)], context=context)
        appointment_pool.write(cr, uid, appointment_ids, {'state': 'invoiced'})
        return True
    
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        doctor_pool = self.pool.get('medical.physician')
        inv_vals = super(medical_sale_pricelist, self)._prepare_invoice(cr, uid, order, lines, context=None)
        doctor_id = doctor_pool.search(cr, uid, [('partner_id.user_id.id', '=', order.user_id.id),('journal_id','!=',False)], context=context)
        if doctor_id:
            doctor_id = doctor_pool.browse(cr, uid, doctor_id[0], context=context)
            inv_vals['journal_id'] = doctor_id.journal_id.id
        else:
            journal_pool = self.pool.get('account.journal')
            invoice_pool = self.pool.get('account.invoice')
            sale_journal = journal_pool.search(cr, uid, [('code','=',_('SAJ'))],context=context)  ## problemas con la traducción del código
            inv_vals['journal_id'] = sale_journal[0] if sale_journal else invoice_pool._default_journal(cr, uid).id


        return inv_vals
    
medical_sale_pricelist()


class medical_physician(osv.osv):
    _inherit = "medical.physician"

    _columns = {
        'pricelist_ids': fields.one2many('product.pricelist', 'doctor_id', 'Pricelists'),
        'journal_id': fields.many2one('account.journal', string='Journal'),
    }
    
    def open_journal_action(self, cr, uid, ids, context=None):
        if not context.get('res_id', False):
            journal_pool = self.pool.get('account.journal')
            sale_journal = journal_pool.search(cr, uid, [('code','=',_('SAJ'))],context=context)
            if sale_journal:
                doctor = self.browse(cr, uid, ids, context=context)[0]
                code = self.pool.get('ir.sequence').next_by_code(cr, uid, 'medical.journal')
                data = journal_pool.copy_data(cr, uid, sale_journal[0], default={'name': doctor.name, 'code': code}, context=context)
                doctor_journal = journal_pool.create(cr, uid, data, context)
                journal_pool.copy_translations(cr, uid, sale_journal[0], doctor_journal, context)
                
                self.write(cr, uid, doctor.id, {'journal_id': doctor_journal}, context=context)
                context['res_id'] = doctor_journal
        act_window = self.pool.get('medical.patient.evaluation')._get_act_window_dict(cr, uid, 'medical_invoice.medical_journal_action', context)
        act_window['res_id'] = context.get('res_id', False)
        return act_window
medical_physician()


class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    
    _columns = {
        'tax_id': fields.many2one('account.tax', string='Taxes', readonly=True, states={'draft': [('readonly', False)]}),
    }

    #to pass update_tax = False
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=False, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        return super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty,
            uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
            lang=lang, update_tax=False, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)

sale_order_line()


class medical_patient_evaluation(osv.osv):
    _name = "medical.patient.evaluation"
    _inherit = _name

    def create(self, cr, uid, values, context=None):
        ret = super(medical_patient_evaluation, self).create(cr, uid, values, context=context)
        context = dict(context or {})
        obj = self.browse(cr, uid, [ret], context=context)
        if not obj.appointment_id:
            pricelist_id = obj.doctor.pricelist_ids[0] if obj.doctor.pricelist_ids else False
            seq = self.pool.get('ir.sequence').next_by_code(cr, uid, 'sale.order', context=context)
            vals = {
                'name': 'Evaluation [%s %s]' % (obj.name.curp, seq),  # ??
                'date_order': obj.evaluation_date,
                'partner_id': obj.name.partner_id.id,
                'user_id': obj.doctor.partner_id.user_id.id,

                'evaluation': ret
            }
            if obj.spec_consultations:
                vals.update({'order_line': [[0, 0, {
                    'name': obj.spec_consultations.name,
                    'price_unit': obj.spec_consultations.list_price,
                    'product_id': obj.spec_consultations.id,
                }]]})
            if pricelist_id:
                vals.update({'pricelist_id': pricelist_id.id, 'currency_id': pricelist_id.currency_id.id,
                             'doctor_pricelist_ids': [[6, 0, [item.id for item in obj.doctor.pricelist_ids]]]})

            sale_id = self.pool.get('sale.order').create(cr, uid, vals, context=context)
            self.pool.get('sale.order').update_evaluation_pendents(cr, uid, ids=[sale_id], context=context)
        else:
            if not obj.appointment_id.sale_id:
                obj.appointment_id.make_sale_order()
            sale_id = obj.appointment_id.sale_id.id
            self.pool.get('sale.order').write(cr, uid, sale_id, {'evaluation': ret}, context=context)
            self.pool.get('sale.order').update_evaluation_pendents(cr, uid, ids=sale_id, context=context)
        return ret

    def write(self, cr, uid, ids, values, context=None):
        context = dict(context or {})
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        ret_ids = super(medical_patient_evaluation, self).write(cr, uid, ids, values, context=context)
        sale_ids = self.pool.get('sale.order').search(cr, uid, [('evaluation', 'in', ids)])

        self.pool.get('sale.order').update_evaluation_pendents(cr, uid, ids=sale_ids, context=context)

        return ret_ids

class medical_product_template(osv.osv):
    _name = "product.template"
    _inherit = 'product.template'

    _columns = {
        'commision': fields.float('Commision', digits_compute=dp.get_precision('Product Price'), help="Salesman Comission."),
    }

medical_product_template()

class stock_location_route(osv.osv):
    _name = 'stock.location.route'
    _inherit = 'stock.location.route'

    _columns = {
        'name': fields.char('Route Name', required=True, translate=True),

    }
stock_location_route()
