odoo.define('browser_pdf', function (require) {
    var core = require('web.core');
    var Model = require('web.Model');

    function browser_pdf(element, action) {
        var ids = action.context.active_ids;
        new Model('report').call('get_action_html', [
            ids, action.report_name, action.data, action.context
        ]).then(function(res) {
            var paper_format = res.paper_format;
            printJS({printable_html:res.content, type:'html'});
        });
    };
    core.action_registry.add('browser_pdf', browser_pdf);


    var ReportAction = require('report.client_action');

    ReportAction.include({
        on_click_print: function () {
            var action = {
                'type': 'ir.actions.client',
                'tag': 'browser_pdf',
                'report_type': 'qweb-pdf',
                'report_name': this.report_name,
                'report_file': this.report_file,
                //'ids': self.ids,
                'data': this.data,
                'context': this.context,
                'display_name': this.title,
            };
            return this.do_action(action);
        },
    });
});