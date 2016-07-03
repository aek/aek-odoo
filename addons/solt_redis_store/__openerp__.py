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


{
    'name': 'Solt Redis Store',
    'version': '1.0',
    'author': 'Soltein S.A de CV',
    'category' : 'tools',
    "website": "http://soltein.org/",
    "depends": ['base'],
    'description' : """
    This module is for add Redis Support to OpenERP
    """,
    "data": [
         'view/solt_redis_store_view.xml'
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'active': False,
    'application': False
}
