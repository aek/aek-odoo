odoo.define('aek_autorefresh.views', function (require) {
    "use strict";

	var core = require('web.core');
	var Model = require('web.DataModel');
    var ListView = require('web.ListView');
    var FormView = require('web.FormView');
    var CalendarView = require('web_calendar.CalendarView');
    var GraphView = require('web.GraphView');
    var KanbanView = require('web_kanban.KanbanView');

    var reload_with_auto_refresh = function(self, parent, callback){
        if(parent.action && parent.action.id != undefined){
            new Model('ir.actions.act_window').call('read', [parent.action.id, ['auto_refresh']]).then(function(value){
                if(value.auto_refresh > 0){
					self.refresh_interval = setInterval(_.bind(function(){
						if(self.$el[0].clientWidth != 0){
							callback();
						}
					}, self), value.auto_refresh*1000);
				}
            })
        }
    };

	ListView.include({
		init: function(parent, dataset, view_id, options) {
			var self = this;
			this._super.apply(this, arguments);
            reload_with_auto_refresh(self, parent, function(){
                self.reload();
            });
	    },
	    destroy : function() {
	    	this._super.apply(this, arguments);
	    	if(this.refresh_interval){
	    		clearInterval(this.refresh_interval);
	    	}
	    }
    });
	
	FormView.include({
		init: function(parent, dataset, view_id, options) {
			var self = this;
			this._super.apply(this, arguments);
            reload_with_auto_refresh(self, parent, function(){
                if(self.get("actual_mode") == "view"){
            		self.reload();
				}
            });
	    },
	    destroy : function() {
	    	this._super.apply(this, arguments);
	    	if(this.refresh_interval){
	    		clearInterval(this.refresh_interval);
	    	}
	    }
    });

	CalendarView.include({
		init: function(parent, dataset, view_id, options) {
			var self = this;
			this._super.apply(this, arguments);
			reload_with_auto_refresh(self, parent, function(){
                self.do_search(self.dataset.domain, self.dataset.context, []);
            });
	    },
	    destroy : function() {
	    	this._super.apply(this, arguments);
	    	if(this.refresh_interval){
	    		clearInterval(this.refresh_interval);
	    	}
	    }
    });

	GraphView.include({
		init: function(parent, dataset, view_id, options) {
			var self = this;
			this._super.apply(this, arguments);
            reload_with_auto_refresh(self, parent, function(){
                self.do_search(self.dataset.domain, self.dataset.context, []);
                self.widget.update_data();
            });
	    },
	    destroy : function() {
	    	this._super.apply(this, arguments);
	    	if(this.refresh_interval){
	    		clearInterval(this.refresh_interval);
	    	}
	    }
    });

	KanbanView.include({
		init: function(parent, dataset, view_id, options) {
			var self = this;
			this._super.apply(this, arguments);
			reload_with_auto_refresh(self, parent, function(){
                self.do_search(self.search_domain, self.search_context, self.group_by_field && [self.group_by_field] || []);
            });
	    },
	    destroy : function() {
	    	this._super.apply(this, arguments);
	    	if(this.refresh_interval){
	    		clearInterval(this.refresh_interval);
	    	}
	    }
    });

});