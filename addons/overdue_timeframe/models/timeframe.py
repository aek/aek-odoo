# -*- encoding: utf-8 -*-

from openerp import fields, models

class overdue_timeframe(models.Model):
    _name = "overdue.timeframe"

    name = fields.Char(string='Timeframe Name', size=64, required=True)
    before_day = fields.Integer(string='Before Day', required=True)
    until_day = fields.Integer(string='Until Day')
    color = fields.Char(string="Color")
