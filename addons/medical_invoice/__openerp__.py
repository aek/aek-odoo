# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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

{
    "name" : "Medical Invoice",
    "version" : "0.1",
    "author" : "Soltein SA de CV",
    "description" : """ 
        This module add functionality to create invoices for doctor's consulting charge.

        Features:
        -Invoice of multiple appointments at a time.
        """,
    "website" : "http://www.soltein.org",
    "depends" : ["medical", "medical_lab",],
    "category" : "Generic Modules/Others",
    "init_xml" : [],
    "demo_xml" : [],
    "data" : [
        "wizard/move_line_to_invoice.xml",
        "medical_invoice_view.xml",
        "wizard/sale_line_invoice.xml",
        "wizard/sale_make_invoice_advance.xml",
        "view/medical_sale_view.xml"
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
