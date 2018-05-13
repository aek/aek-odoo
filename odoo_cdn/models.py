# -*- coding: utf-8 -*-

import itertools
import re
import urlparse
import hashlib

from lxml import html

from odoo import api, models, fields
from odoo.tools import html_escape as escape
from odoo.addons.base.ir import ir_qweb
from odoo.http import request


class QWeb(models.AbstractModel):
    _inherit = 'ir.qweb'

    def check_cdn_node_attrs(self, el):
        for attr in el.attrib.keys():
            if (attr == self.URL_ATTRS.get(el.tag) or attr == self.CDN_TRIGGERS.get(el.tag)):
                attr_value = request.website.get_cdn_url(el.attrib.get(attr))
                el.set(attr, attr_value)

        if el.getchildren():
            for item in el:
                item = self.check_cdn_node_attrs(item)
        return el

    def _get_field(self, record, field_name, expression, tagName, field_options, options, values):
        t_attrs, content, force_display = super(QWeb, self)._get_field(record, field_name, expression, tagName, field_options, options, values)
        field = record._fields[field_name]
        if field.type == 'html' and content and request and getattr(request, 'website', None) and request.website.cdn_activated:
            el = self.check_cdn_node_attrs(html.fromstring(content))
            content = html.tostring(el).encode('utf8')
        return (t_attrs, content, force_display)

class Image(models.AbstractModel):
    _inherit = 'ir.qweb.field.image'

    @api.model
    def record_to_html(self, record, field_name, options):
        assert options['tagName'] != 'img',\
            "Oddly enough, the root tag of an image field can not be img. " \
            "That is because the image goes into the tag, or it gets the " \
            "hose again."

        aclasses = ['img', 'img-responsive'] + options.get('class', '').split()
        classes = ' '.join(itertools.imap(escape, aclasses))

        max_size = None
        if options.get('resize'):
            max_size = options.get('resize')
        else:
            max_width, max_height = options.get('max_width', 0), options.get('max_height', 0)
            if max_width or max_height:
                max_size = '%sx%s' % (max_width, max_height)

        sha = hashlib.sha1(getattr(record, '__last_update')).hexdigest()[0:7]
        max_size = '' if max_size is None else '/%s' % max_size
        src = '/web/image/%s/%s/%s%s?unique=%s' % (record._name, record.id, field_name, max_size, sha)
        if request and getattr(request, 'website', None) and request.website.cdn_activated:
            src = request.website.get_cdn_url(src)

        alt = None
        if options.get('alt-field') and getattr(record, options['alt-field'], None):
            alt = escape(record[options['alt-field']])
        elif options.get('alt'):
            alt = options['alt']

        src_zoom = None
        if options.get('zoom') and getattr(record, options['zoom'], None):
            src_zoom = '/web/image/%s/%s/%s%s?unique=%s' % (record._name, record.id, options['zoom'], max_size, sha)

            if request and getattr(request, 'website', None) and request.website.cdn_activated:
                src_zoom = request.website.get_cdn_url(src_zoom)

        elif options.get('zoom'):
            src_zoom = options['zoom']


        img = '<img class="%s" src="%s" style="%s"%s%s/>' % \
            (classes, src, options.get('style', ''), ' alt="%s"' % alt if alt else '', ' data-zoom="1" data-zoom-image="%s"' % src_zoom if src_zoom else '')
        return ir_qweb.unicodifier(img)

class Website(models.Model):
    _inherit = "website"

    @api.model
    def get_cdn_url(self, uri):
        if request and request.website and not request.debug:
            cdn_url = request.website.cdn_url
            cdn_filters = (request.website.cdn_filters or '').splitlines()
            for flt in cdn_filters:
                if flt and re.match(flt, uri):
                    return urlparse.urljoin(cdn_url, uri)
        return uri