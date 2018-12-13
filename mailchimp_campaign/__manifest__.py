# -*- coding: utf-8 -*-
{
    'name': 'Export from Mass Mailing to Mailchimp',
    'version': '1.0',
    'author': 'Axel Mendoza',
    'website': 'https://www.aekroft.com',
    'category': 'CRM',
    'description': """
Module to manage Campaigns on Mailchimp.
========================================


    """,
    'depends': ['base', 'mass_mailing', 'hr'],
    'data':[
        'views/mailchimp_campaign.xml',
    ],
    'installable': True,

}
