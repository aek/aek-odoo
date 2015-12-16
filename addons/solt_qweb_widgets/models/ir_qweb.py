# -*- coding: utf-8 -*-
import logging
import werkzeug

import copy
from lxml import etree

import simplejson

from openerp import http, models, fields, tools, SUPERUSER_ID

from openerp.osv import osv, orm
from openerp.http import request

from openerp.addons.base.ir.ir_qweb import HTMLSafe, QWebContext, QWebException

from openerp.addons.website_sale.controllers.main import QueryURL, get_pricelist, website_sale

_logger = logging.getLogger(__name__)


PPG = 20 # Products Per Page
PPR = 4  # Products Per Row

class table_compute(object):
    def __init__(self):
        self.table = {}

    def _check_place(self, posx, posy, sizex, sizey):
        res = True
        for y in range(sizey):
            for x in range(sizex):
                if posx+x>=PPR:
                    res = False
                    break
                row = self.table.setdefault(posy+y, {})
                if row.setdefault(posx+x) is not None:
                    res = False
                    break
            for x in range(PPR):
                self.table[posy+y].setdefault(x, None)
        return res

    def process(self, elements):
        # Compute elements positions on the grid
        minpos = 0
        index = 0
        maxy = 0
        for p in elements:
            x = min(max(p.website_size_x, 1), PPR)
            y = min(max(p.website_size_y, 1), PPR)
            if index>=PPG:
                x = y = 1

            pos = minpos
            while not self._check_place(pos%PPR, pos/PPR, x, y):
                pos += 1
            # if 21st products (index 20) and the last line is full (PPR products in it), break
            # (pos + 1.0) / PPR is the line where the product would be inserted
            # maxy is the number of existing lines
            # + 1.0 is because pos begins at 0, thus pos 20 is actually the 21st block
            # and to force python to not round the division operation
            if index >= PPG and ((pos + 1.0) / PPR) > maxy:
                break

            if x==1 and y==1:   # simple heuristic for CPU optimization
                minpos = pos/PPR

            for y2 in range(y):
                for x2 in range(x):
                    self.table[(pos/PPR)+y2][(pos%PPR)+x2] = False
            self.table[pos/PPR][pos%PPR] = {
                'elem': p, 'x':x, 'y': y,
                'class': " "#.join(map(lambda x: x.html_class or '', p.website_style_ids or []))
            }
            if index<=PPG:
                maxy=max(maxy,y+(pos/PPR))
            index += 1

        # Format table according to HTML needs
        rows = self.table.items()
        rows.sort()
        rows = map(lambda x: x[1], rows)
        for col in range(len(rows)):
            cols = rows[col].items()
            cols.sort()
            x += len(cols)
            rows[col] = [c for c in map(lambda x: x[1], cols) if c != False]

        return rows


class WebsiteProducts(orm.AbstractModel):
    _name = 'ir.qweb.widget.website_products'
    _inherit = 'ir.qweb.widget'

    #def record_to_html(self, cr, uid, field_name, record, options=None, context=None):
    def _format(self, inner, options, qwebcontext):
        if options is None:
            options = {}
        record = self.pool['ir.qweb'].eval(inner, qwebcontext)
        domain = []
        if options.get('domain', False):
            domain += options.get('domain')
        template = options.get('template')
        product_obj = self.pool.get('product.template')

        url = "/shop"
        product_count = product_obj.search_count(qwebcontext.cr, SUPERUSER_ID, domain)

        pager = record.pager(url=url, total=product_count, page=0, step=PPG, scope=7, url_args={})
        product_ids = product_obj.search(qwebcontext.cr, SUPERUSER_ID, domain, limit=PPG, offset=pager['offset'], order='website_published desc, website_sequence desc')
        products = product_obj.browse(qwebcontext.cr, SUPERUSER_ID, product_ids)

        style_obj = self.pool['product.style']
        style_ids = style_obj.search(qwebcontext.cr, SUPERUSER_ID, [])
        styles = style_obj.browse(qwebcontext.cr, SUPERUSER_ID, style_ids)

        category_obj = self.pool['product.public.category']
        category_ids = category_obj.search(qwebcontext.cr, SUPERUSER_ID, [('parent_id', '=', False)])
        categs = category_obj.browse(qwebcontext.cr, SUPERUSER_ID, category_ids)

        attributes_obj = self.pool['product.attribute']
        attributes_ids = attributes_obj.search(qwebcontext.cr, SUPERUSER_ID, [])
        attributes = attributes_obj.browse(qwebcontext.cr, SUPERUSER_ID, attributes_ids)

        partner = self.pool['res.users'].browse(qwebcontext.cr, SUPERUSER_ID, SUPERUSER_ID).partner_id
        pricelist = partner.property_product_pricelist

        from_currency = self.pool.get('product.price.type')._get_field_currency(qwebcontext.cr, SUPERUSER_ID, 'list_price', qwebcontext.context)
        to_currency = pricelist.currency_id
        compute_currency = lambda price: self.pool['res.currency']._compute(qwebcontext.cr, SUPERUSER_ID, from_currency, to_currency, price)

        keep = QueryURL('/shop')

        values = {
            'search': '',
            'category': None,
            'attrib_values': [],
            'attrib_set': set(),
            'pager': pager,
            'pricelist': pricelist,
            'products': products,
            'bins': table_compute().process(products),
            'rows': PPR,
            'PPG':PPG,
            'styles': styles,
            'categories': categs,
            'attributes': attributes,
            'compute_currency': compute_currency,
            'keep': keep,
            'style_in_product': lambda style, product: style.id in [s.id for s in product.website_style_ids],
            'attrib_encode': lambda attribs: werkzeug.url_encode([('attrib',i) for i in attribs]),
        }

        html = self.pool["ir.ui.view"].render(qwebcontext.cr, SUPERUSER_ID, template, values, engine='ir.qweb').decode('utf8')

        return HTMLSafe(html)

class WebsiteProductsDetails(orm.AbstractModel):
    _name = 'ir.qweb.widget.website_products_details'
    _inherit = 'ir.qweb.widget'

    def get_attribute_value_ids(self, product):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        currency_obj = pool['res.currency']
        attribute_value_ids = []
        visible_attrs = set(l.attribute_id.id
                                for l in product.attribute_line_ids
                                    if len(l.value_ids) > 1)
        if request.website.pricelist_id.id != context['pricelist']:
            website_currency_id = request.website.currency_id.id
            currency_id = self.get_pricelist().currency_id.id
            for p in product.product_variant_ids:
                price = currency_obj.compute(cr, uid, website_currency_id, currency_id, p.lst_price)
                attribute_value_ids.append([p.id, [v.id for v in p.attribute_value_ids if v.attribute_id.id in visible_attrs], p.price, price])
        else:
            attribute_value_ids = [[p.id, [v.id for v in p.attribute_value_ids if v.attribute_id.id in visible_attrs], p.price, p.lst_price]
                for p in product.product_variant_ids]

        return attribute_value_ids

    def _format(self, inner, options, qwebcontext):
        product = qwebcontext.get('product')
        category = ''
        search = ''

        cr, uid, context, pool = qwebcontext.cr, SUPERUSER_ID, qwebcontext.context, self.pool
        category_obj = pool['product.public.category']
        template_obj = pool['product.template']

        context.update(active_id=product.id)

        if category:
            category = category_obj.browse(cr, uid, int(category), context=context)

        # attrib_list = request.httprequest.args.getlist('attrib')
        # attrib_values = [map(int,v.split("-")) for v in attrib_list if v]
        # attrib_set = set([v[1] for v in attrib_values])

        keep = QueryURL('/shop', category=category and category.id, search=search, attrib=[])#attrib_list

        category_ids = category_obj.search(cr, uid, [], context=context)
        category_list = category_obj.name_get(cr, uid, category_ids, context=context)
        category_list = sorted(category_list, key=lambda category: category[1])

        pricelist = get_pricelist()

        from_currency = pool.get('product.price.type')._get_field_currency(cr, uid, 'list_price', context)
        to_currency = pricelist.currency_id
        compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)

        if not request.context.get('pricelist'):
            request.context['pricelist'] = int(get_pricelist())
            # product = template_obj.browse(cr, uid, int(product), context=context)

        values = {
            'search': search,
            'category': category,
            'pricelist': pricelist,
            'attrib_values': [],#attrib_values,
            'compute_currency': compute_currency,
            'attrib_set': set(),#attrib_set,
            'keep': keep,
            'category_list': category_list,
            'main_object': product,
            'product': product,
            'get_attribute_value_ids': self.get_attribute_value_ids
        }
        qwebcontext.update(values)

        html = pool["ir.qweb"].render_node(inner, qwebcontext).decode('utf8')
        return HTMLSafe(html)


class WebsitePartners(orm.AbstractModel):
    _name = 'ir.qweb.widget.website_partners'
    _inherit = 'ir.qweb.widget'

    def _format(self, inner, options, qwebcontext):
        if options is None:
            options = {}
        record = self.pool['ir.qweb'].eval(inner, qwebcontext)
        domain = []
        if options.get('domain', False):
            domain += options.get('domain')
        template = options.get('template')
        partner_obj = self.pool.get('res.partner')

        url = "/partners"
        partner_count = partner_obj.search_count(qwebcontext.cr, SUPERUSER_ID, domain)

        pager = record.pager(url=url, total=partner_count, page=0, step=PPG, scope=7, url_args={})
        partner_ids = partner_obj.search(qwebcontext.cr, SUPERUSER_ID, domain, limit=PPG, offset=pager['offset'], order='website_published desc, website_sequence desc')
        partners = partner_obj.browse(qwebcontext.cr, SUPERUSER_ID, partner_ids)

        category_obj = self.pool['res.partner.category']
        category_ids = category_obj.search(qwebcontext.cr, SUPERUSER_ID, [('parent_id', '=', False)])
        categs = category_obj.browse(qwebcontext.cr, SUPERUSER_ID, category_ids)

        keep = QueryURL('/')

        values = {
            'search': '',
            'category': None,
            'pager': pager,
            'partners': partners,
            'bins': table_compute().process(partners),
            'rows': PPR,
            'PPG': PPG,
            'categories': categs,
            'keep': keep,
        }

        html = self.pool["ir.ui.view"].render(qwebcontext.cr, SUPERUSER_ID, template, values, engine='ir.qweb').decode('utf8')

        return HTMLSafe(html)

class solt_qweb_mixin(object):

    def render_tag_call_xpath(self, element, template_attributes, generated_attributes, qwebcontext):
        if not len(element):
            template = qwebcontext.get('__template__')
            raise QWebException("t-call-xpath need to contain children nodes", template=template)

        d = qwebcontext.copy()
        d[0] = self.render_element(element, template_attributes, generated_attributes, d)
        cr = d.get('request') and d['request'].cr or None
        uid = d.get('request') and d['request'].uid or None

        template = self.eval_format(template_attributes["call-xpath"], d)
        try:
            template = int(template)
        except ValueError:
            pass

        if qwebcontext is None:
            qwebcontext = {}

        if not isinstance(qwebcontext, QWebContext):
            def loader(name):
                return self.read_template(cr, uid, name, context=d)
            qwebcontext = QWebContext(cr, uid, qwebcontext, loader=loader, context=d)

        qwebcontext['__template__'] = template
        stack = qwebcontext.get('__stack__', [])
        if stack:
            qwebcontext['__caller__'] = stack[-1]
        stack.append(template)
        qwebcontext['__stack__'] = stack
        qwebcontext['xmlid'] = str(stack[0]) # Temporary fix

        inner = self.get_template(template, qwebcontext)#self.render(cr, uid, template, d)
        res_nodes = []
        for spec in element:
            if spec.tag == 'xpath':
                nodes = inner.xpath(spec.get('expr'))
                for node in nodes:
                    if node is not None:
                        pos = spec.get('position', 'childs')
                        if pos == 'childs':
                            for child in node:
                                res_nodes.append(copy.deepcopy(child))
                        # elif pos == 'attributes':
                        #     for child in spec.getiterator('attribute'):
                        #         attribute = (child.get('name'), child.text or None)
                        #         if attribute[1]:
                        #             node.set(attribute[0], attribute[1])
                        #         elif attribute[0] in node.attrib:
                        #             del node.attrib[attribute[0]]
                        # else:
                        #     sib = node.getnext()
                        #     for child in spec:
                        #         if pos == 'inside':
                        #             node.append(child)
                        #         elif pos == 'after':
                        #             if sib is None:
                        #                 node.addnext(child)
                        #                 node = child
                        #             else:
                        #                 sib.addprevious(child)
                        #         elif pos == 'before':
                        #             node.addprevious(child)
        options = simplejson.loads(template_attributes.get('call-options') or '{}')
        #inner = "".join(map(lambda el: etree.tostring(el), res_nodes))

        node_root = etree.Element('div')
        node_root.set('class','row')

        if options.get('widget', False):
            widget = self.get_widget_for(options.get('widget'))
            for node in res_nodes:
                node_root.append(node)
            return widget.format(node_root, options, qwebcontext)

        return inner

class solt_ir_qweb(orm.AbstractModel, solt_qweb_mixin):
    _inherit = 'ir.qweb'

class solt_website_qweb(orm.AbstractModel, solt_qweb_mixin):
    _inherit = 'website.qweb'
