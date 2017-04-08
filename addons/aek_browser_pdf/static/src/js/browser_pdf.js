openerp.aek_browser_pdf = function (instance) {

    instance.web.aek_browser_pdf = function(element, action) {
        var ids = Array.isArray(action.params.ids) ? action.params.ids : [action.params.ids];
        new instance.web.Model('report').call('get_action_html', [
            ids, action.params.report_name, action.params.data, action.params.context
        ]).then(function(res) {
            var paper_format = res.paper_format;
            printJS({printable_html:res.content, type:'html'});
        });
    };
    instance.web.client_actions.add("aek_browser_pdf", "instance.web.aek_browser_pdf");
};

