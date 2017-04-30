{
    'name' : 'POS Receipt Dual Lang',
    'version': '0.1',
    'category': 'Tools',
    'complexity': 'easy',
    'description':"""This module provides Dual Lang Receipt for Odoo Point of Sale.""",
    'data': [
        'assets.xml',
    ],
    'depends' : ['point_of_sale'],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'auto_install': False,
}
