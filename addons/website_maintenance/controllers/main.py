import logging
from openerp.http import request
from openerp.addons.web import http

logger = logging.getLogger(__name__)

class WebsiteMaintenance(http.Controller):

    @http.route('/website/maintenance', type='http', auth="public", website=True)
    def page_maintenance(self):
        values = {
            'status_message': request.website.maintenance_message or "We're having a maintenance now",
            'status_code': 503,
            'company_email': request.env.user.company_id.email
        }
        return request.website.render('website_maintenance.maintenance_message', values)

    @http.route('/website/maintenance_status', type='json', auth="public", website=True)
    def page_maintenance_status(self):
        return {"maintenance": request.website.maintenance_mode}