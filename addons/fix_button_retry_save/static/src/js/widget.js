openerp.fix_button_retry_save = function(instance) {

    instance.web.FormView.include({
        record_saved: function (r) {
            _(this.fields).each(function (field, f) {
                field._dirty_flag = false;
            });
            return this._super.apply(this, arguments);
        }
    })
};