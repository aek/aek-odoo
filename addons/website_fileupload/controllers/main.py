# -*- coding: utf-8 -*-
import base64

from openerp import http, SUPERUSER_ID
from openerp.http import request


class FileUploadController(http.Controller):

    @http.route('/website/fileupload', type='http', auth='public', website=True, multilang=False, methods=['POST'])
    def submit_form(self, **kwargs):
        request.env['website.custom.file.upload'].sudo().create({
            'name': kwargs['file'].filename,
            'file': base64.encodestring(kwargs['file'].stream.read()),
        })
