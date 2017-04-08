openerp.aek_website_maintenance = function (instance) {
    openerp.Session.include({
        rpc: function(url, params, options) {
            var self = this;
            p = this._super.apply(this, arguments);

            return p.fail(function(error, event) { // Allow deferred user to disable rpc_error call in fail
                var res = false;
                /*$.ajax({
                    async: false,
                    data: JSON.stringify({r: {status: true}, jsonp: 'jsonp'}),
                    url: '/website/maintenance_status',
                    dataType: 'json',
                    type: 'GET',
                    contentType: 'application/json',
                    success: function(result){
                        res = result;
                    }
                });*/
                self.alive(openerp.jsonRpc('/website/maintenance_status', 'call', {}).then(function(data) {
                    res = data;
                    if(res && res.maintenance){
                        event.preventDefault();
                        instance.web.redirect('/website/maintenance');
                    }
                }));

            });
        },
    });
}
