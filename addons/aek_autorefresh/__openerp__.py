# -*- coding: utf-8 -*-
{
    'name': 'Auto Refresh Views',
    'version': '0.1',
    'category': 'web',
    'description': """This module use the auto_refresh field of OpenERP actions to set a time based refresh of views used on the actions.
    Useful for auto-refresh Trees, Forms, Kanban, Graphs, Calendar""",
    'author': 'aekroft@gmail.com',
    'website': 'https://aekroft.com',
    'depends': ['base', 'web', 'web_calendar', 'web_graph', 'web_kanban'],
    'data': ['assets.xml'],
    'active': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
