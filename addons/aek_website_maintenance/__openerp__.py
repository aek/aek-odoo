{
    'name': 'Website Maintenance Status',
    'version': '1.0',
    'category': 'Website',
    'description': """This module handle the maintenance for Odoo website.""",
    'author': 'aekroft@gmail.com',
    'website': 'https://aekroft.com',
    'summary': '',
    'depends': ['website'],
    'data': [
        'view/website_maintenance_templates.xml',
        'view/res_config.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': True,
}
