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

from openerp import api, fields, models, _


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = _name

    appointment = fields.Many2one('medical.appointment')
    evaluation = fields.Many2one('medical.patient.evaluation')

    @api.multi
    def update_evaluation_pendents(self):
        # TODO : don't work then items are remove from evaluation
        for sale in self:
            if not sale.evaluation and not (sale.appointment and bool(sale.appointment.evaluation_ids)):
                return
            exist_prod_ids = [l.product_id.id for l in sale.order_line if bool(l.product_id)]
            evaluation = sale.evaluation if sale.evaluation else sale.appointment.evaluation_ids[0]
            order_lines = []
            #  add medicament
            _name_get = lambda prod: prod.name_get()[0][1]
            for po in evaluation.prescription_order_ids:
                for line in po.prescription_line:
                    prod = line.medicament.name
                    if prod.id not in exist_prod_ids:
                        order_lines.append((0, 0, {
                            'product_uom_qty': line.refills,
                            'product_id': prod.id,
                            'name': _('Medicament: ') + prod.name
                            }))
            #  add lab tests
            for order in evaluation.lab_test_ids:
                for test in order.test_ids:
                    prod = test.inherit_id
                    if prod.id not in exist_prod_ids:
                        order_lines.append((0, 0, {
                            'product_id': prod.id,
                            'name': _('Lab test: ') + _name_get(test)
                        }))
            #  add imagenology studies
            for order in evaluation.imagenology_order_ids:
                for line in order.imagenology_study_ids:
                    prod = line.study.product_id
                    if prod.id not in exist_prod_ids:
                        order_lines.append((0, 0, {
                            'product_id': prod.id,
                            'name': _('Imagenology study: ') + _name_get(line.study)
                        }))
            # add procedures
            for action in evaluation.actions:
                prod = action.procedure.product_id
                if prod.id not in exist_prod_ids:
                    order_lines.append((0, 0, {
                        'product_id': prod.id,
                        'name': _('Medical procedure: ') + _name_get(action.procedure)
                    }))
            if order_lines:
                sale.write({'order_line': order_lines})
        return True

    _defaults = {

        'user_id': False,

    }
#===============================================================================
# 
#     @api.multi
#     def write(self, vals):
#         ret = super(SaleOrder, self).write(vals)
#         state = vals.get('state', False)
#         if state and state == 'progress':
#             for obj in self:
#                 if obj.evaluation.prescription_order.invoice_status == 'tobe':
#                     obj.evaluation.prescription_order.write({'invoice_status': 'invoiced'})
#         return ret
#===============================================================================
