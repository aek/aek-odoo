from odoo import http
from odoo.http import request
import itertools
import operator

class GetTranslations(http.Controller):

    @http.route('/pos/translations', type='json', auth="none")
    def translations(self, mods=None, lang=None):
        request.disable_db = False
        if mods is None:
            mods = [x['name'] for x in request.env['ir.module.module'].sudo().search_read(
                [('state', '=', 'installed')], ['name'])]
        if lang is None:
            lang = request.context["lang"]
        langs = request.env['res.lang'].sudo().search([("code", "=", lang)])
        lang_params = None
        if langs:
            lang_params = langs.read([
                "name", "direction", "date_format", "time_format",
                "grouping", "decimal_point", "thousands_sep"])[0]

        # Regional languages (ll_CC) must inherit/override their parent lang (ll), but this is
        # done server-side when the language is loaded, so we only need to load the user's lang.
        translations_per_module = {}
        messages = request.env['ir.translation'].sudo().search_read([
            ('module', 'in', mods), ('lang', '=', lang),
            ('value', '!=', False),
            ('value', '!=', '')],
            ['module', 'src', 'value', 'lang'], order='module')
        for mod, msg_group in itertools.groupby(messages, key=operator.itemgetter('module')):
            translations_per_module.setdefault(mod, {'messages': []})
            translations_per_module[mod]['messages'].extend({
                'id': m['src'],
                'string': m['value']}
                for m in msg_group)
        return {
            'lang_parameters': lang_params,
            'modules': translations_per_module,
            'multi_lang': len(request.env['res.lang'].sudo().get_installed()) > 1,
        }