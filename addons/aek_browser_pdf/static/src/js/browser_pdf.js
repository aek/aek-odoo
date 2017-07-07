odoo.define('aek_browser_pdf', function (require) {
    var core = require('web.core');
    var Model = require('web.Model');

    function aek_browser_pdf(element, action) {
        var ids = Array.isArray(action.params.ids) ? action.params.ids : [action.params.ids];
        new Model('report').call('get_action_html', [
            ids, action.params.report_name, action.params.data, action.params.context
        ]).then(function(res) {
            var paper_format = res.paper_format;
            printJS({printable_html:res.content, type:'html'});
        });
    };
    core.action_registry.add('aek_browser_pdf', aek_browser_pdf);
});