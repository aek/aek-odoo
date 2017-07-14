openerp.aek_browser_pdf = function (instance) {

    instance.web.aek_browser_pdf = function(element, action) {
        var ids = action.context.active_ids;
        new instance.web.Model('report').call('get_action_html', [
            ids, action.report_name, action.data, action.context
        ]).then(function(res) {
            var paper_format = res.paper_format;
            printJS({printable_html:res.content, type:'html'});
        });
    };
    instance.web.client_actions.add("aek_browser_pdf", "instance.web.aek_browser_pdf");
};

