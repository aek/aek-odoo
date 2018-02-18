openerp.fix_o2m_onchange = function(instance) {

    instance.web.form.One2ManyListView.include({
        changed_records: function () {}
    })

};