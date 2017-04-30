odoo.define('pos_receipt_dual_lang', function (require) {
    var core = require('web.core');
    var _t = core._t;
    var QWeb = core.qweb;
    var session = require('web.session');

    var Model = require('web.Model');
    var translation = require('web.translation');
    var screens = require('point_of_sale.screens');

    translation.TranslationDataBase.include({
        init: function() {
            this._super();
            this.swap_db = false;
        },
        get: function(key) {
            if(this.swap_db){
                return this.swap_db[key];
            }
            return this.db[key];
        },
        swap: function(swap_db){
            var ret = {};
            for(var key in swap_db){
                if(this.db[key]){
                    ret[this.db[key]] = swap_db[key];
                } else {
                    ret[key] = swap_db[key];
                }
            }
            this.swap_db = ret;
        }
    });

    var _t_dual = false;
    session.on('module_loaded', this, function () {
        new Model("ir.config_parameter").call("get_param", ["pos_receipt_dual_lang"]).then(function(dual_lang) {
            if (!!dual_lang) {
                _t_dual = new translation.TranslationDataBase().build_translation_function();
                _t_dual.database.load_translations(session, ['point_of_sale'], dual_lang);
            }
        });

    });

    screens.ReceiptScreenWidget.include({
        render_receipt: function() {
            var order = this.pos.get_order();
            var receipt_data = {
                widget:this,
                order: order,
                receipt: order.export_for_printing(),
                orderlines: order.get_orderlines(),
                paymentlines: order.get_paymentlines(),
            };
            QWeb.compiled_templates['PosTicket'] = false;
            var orig_html = QWeb.render('PosTicket', receipt_data);
            var dual_html =  '';
            if(_t_dual){
                translation._t.database.swap(_t_dual.database.db);
                QWeb.compiled_templates['PosTicket'] = false;
                var dual_html = '<br/>' + QWeb.render('PosTicket', receipt_data);
                translation._t.database.swap_db = false;
            }
            this.$('.pos-receipt-container').html(orig_html + dual_html);
        }
    })

});
// vim:et fdc=0 fdl=0:
