# -*- coding: utf-8 -*-
{
    'name': 'Overdue Timeframes',
    'version': '1.0',
    'author': 'Axel Mendoza',
    'category' : 'account',
    "website": "http://aekroft.com/",
    "depends": ['base', 'account'],
    'description' : """
    This module brings you a report with a configurable timeframes to visualize the overdue partner amounts based on validated and unpaid invoices
    """,
    "data": [
        'views/overdue_timeframe_report.xml',
        'views/overdue_timeframe_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'active': False,
    'application': False
}
