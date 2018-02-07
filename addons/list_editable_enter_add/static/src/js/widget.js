openerp.list_editable_enter_add = function(instance) {

    instance.web.ListView.include({
        keypress_ENTER: function () {
            var self = this;
            return this.save_edition().then(function (saveInfo) {
                if (!saveInfo) { return null; }
                return self.start_edition(false, {"focus_field": self.fields_view.arch.attrs.enter_add_focus_field});
            });
        }
    });
};