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

from openerp import api, fields, models


class MoveLineToInvoice(models.TransientModel):
    _name = "move.line.to.invoice"

    def _get_move_lines(self):
        return self.env['account.journal'].browse(self._context.get('active_ids', False))._get_account_move_line_ids().ids

    move_lines = fields.Many2many('account.move.line', default=_get_move_lines)
    select_lines = fields.Boolean(string='Select lines')

    @api.multi
    def generate_invoices(self):
        journal = self.env['account.journal'].browse(self._context.get('active_ids', False))
        return journal.generate_invoice(move_lines=self.move_lines if self.select_lines else None)