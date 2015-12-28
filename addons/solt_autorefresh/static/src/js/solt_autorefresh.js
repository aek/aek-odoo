
openerp.solt_autorefresh = function (instance) {

	instance.web.ListView.include({
		init: function(parent, dataset, view_id, options) {
			var self = this;
			this._super.apply(this, arguments);
			if(parent.action && parent.action.auto_refresh > 0){
				self.refresh_interval = setInterval(_.bind(function(){
					if(this.$el[0].clientWidth != 0){
						this.reload();
					}
				}, self), parent.action.auto_refresh*1000);
			}
	    },
	    destroy : function() {
	    	this._super.apply(this, arguments);
	    	if(this.refresh_interval){
	    		clearInterval(this.refresh_interval);
	    	}
	    }
    });
	
	instance.web.FormView.include({
		init: function(parent, dataset, view_id, options) {
			var self = this;
			this._super.apply(this, arguments);
			if(parent.action && parent.action.auto_refresh > 0){
				self.refresh_interval = setInterval(_.bind(function(){ 
					if(this.$el[0].clientWidth != 0 && this.dataset.index != null){
						this.reload();
					}
				}, self), parent.action.auto_refresh*1000);
			}
	    },
	    destroy : function() {
	    	this._super.apply(this, arguments);
	    	if(this.refresh_interval){
	    		clearInterval(this.refresh_interval);
	    	}
	    }
    });
	
	instance.web_calendar.CalendarView.include({
		init: function(parent, dataset, view_id, options) {
			var self = this;
			this._super.apply(this, arguments);
			if(parent.action && parent.action.auto_refresh > 0){
				self.refresh_interval = setInterval(_.bind(function(){
					if(this.$el[0].clientWidth != 0){
						this.do_search(this.dataset.domain, this.dataset.context, []);
					}
				}, self), parent.action.auto_refresh*1000);
			}
	    },
	    destroy : function() {
	    	this._super.apply(this, arguments);
	    	if(this.refresh_interval){
	    		clearInterval(this.refresh_interval);
	    	}
	    }
    });
	
	instance.web_graph.GraphView.include({
		init: function(parent, dataset, view_id, options) {
			var self = this;
			this._super.apply(this, arguments);
			if(parent.action && parent.action.auto_refresh > 0){
				self.refresh_interval = setInterval(_.bind(function(){ 
					if(this.$el[0].clientWidth != 0){
					    this.search_view.do_search();
					    this.graph_widget.display_data();
					}
				}, self), parent.action.auto_refresh*1000);
					
			}
	    },
	    destroy : function() {
	    	this._super.apply(this, arguments);
	    	if(this.refresh_interval){
	    		clearInterval(this.refresh_interval);
	    	}
	    }
    });
	
	instance.web_kanban.KanbanView.include({
		init: function(parent, dataset, view_id, options) {
			var self = this;
			this._super.apply(this, arguments);
			if(parent.action && parent.action.auto_refresh > 0){
				self.refresh_interval = setInterval(_.bind(function(){
					if(this.$el[0].clientWidth != 0){
						this.do_reload();
					}
				}, self), parent.action.auto_refresh*1000);
					
			}
	    },
	    destroy : function() {
	    	this._super.apply(this, arguments);
	    	if(this.refresh_interval){
	    		clearInterval(this.refresh_interval);
	    	}
	    }
    });
};

