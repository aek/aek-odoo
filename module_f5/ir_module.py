# -*- coding: utf-8 -*-
import logging
import threading

import odoo
from odoo import models, fields, tools, api

_logger = logging.getLogger(__name__)

class ir_module(models.Model):
    _name = "ir.module.module"
    _inherit = ['ir.module.module']
    #_order = 'id'

    @api.multi
    def button_update_self(self):
        registry = odoo.registry(self.env.cr.dbname)
        def process_sql_file(cr, fp):
            queries = fp.read().split(';')
            for query in queries:
                new_query = ' '.join(query.split())
                if new_query:
                    cr.execute(new_query)

        def _get_files_of_kind(kind):
            if kind == 'demo':
                kind = ['demo_xml', 'demo']
            elif kind == 'data':
                kind = ['init_xml', 'update_xml', 'data']
            if isinstance(kind, str):
                kind = [kind]
            files = []
            for k in kind:
                for f in package[k]:
                    files.append(f)
                    if k.endswith('_xml') and not (k == 'init_xml' and not f.endswith('.xml')):
                        correct_key = 'demo' if k.count('demo') else 'data'
                        _logger.warning(
                            "module %s: key '%s' is deprecated in favor of '%s' for file '%s'.",
                            module['name'], k, correct_key, f
                        )
            return files
    
        def _load_data(cr, module_name, idref, mode, kind):
            """

            kind: data, demo, test, init_xml, update_xml, demo_xml.

            noupdate is False, unless it is demo data or it is csv data in
            init mode.

            """
            try:
                if kind in ('demo', 'test'):
                    threading.currentThread().testing = True
                for filename in _get_files_of_kind(kind):
                    _logger.info("loading %s/%s", module_name, filename)
                    noupdate = False
                    if kind in ('demo', 'demo_xml') or (filename.endswith('.csv') and kind in ('init', 'init_xml')):
                        noupdate = True
                    tools.convert_file(cr, module_name, filename, idref, mode, noupdate, kind, registry._assertion_report)
            finally:
                if kind in ('demo', 'test'):
                    threading.currentThread().testing = False
        
        mode = 'update'
        for module in self.read(['name']):
            idref = {}
            models = []
            for cls in odoo.models.MetaModel.module_to_models.get(module['name'], []):
                model_name = cls._name
                if model_name == None:
                    if cls._inherit != None:
                        if isinstance(cls._inherit, (set, list, tuple)):
                            model_name = cls._inherit[0]
                        else:
                            model_name = cls._inherit
                    else:
                        continue

                if model_name != None and model_name not in models:
                    models.append(model_name)
            # models = [self.env[m] for m in models]

            registry.setup_models(self.env.cr)
            registry.init_models(self.env.cr, models, self.env.context)

            package = odoo.modules.module.load_information_from_description_file(module['name'])

            module_id = self.env['ir.module.module'].browse(module['id'])

            module_id._check()

            _load_data(self.env.cr, module['name'], idref, mode, kind='data')
            self.env['ir.ui.view']._validate_module_views(module['name'])
            module_id.with_context(overwrite=True)._update_translations()
        self.env['ir.ui.menu']._parent_store_compute()
        self.env.cr.commit()
        return True
