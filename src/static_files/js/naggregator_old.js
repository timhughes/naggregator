(function($) {

	window.NagiosServer = Backbone.Model.extend({}); 
	
	
	window.NagiosServers = Backbone.Collection.extend({
		model:NagiosServer,
		url: "/api/"
	});
	
	window.library = new NagiosServers();

	setInterval(function () {
		window.library.fetch();
	}, 30000);
	
	window.NagiosServerView = Backbone.View.extend({
		
		tag: 'li',
		className: 'nagios-server',
			
		
		initialize: function() {
			_.bindAll(this, 'render');
			this.model.bind('change', this.render);
			this.template = _.template($('#nagios-server-template').html());
		},
		render: function() {
			var renderedContent = this.template(this.model.toJSON());
			$(this.el).html(renderedContent);
			return this;
		}
	});
	
	window.DashboardNagiosServerView = NagiosServerView.extend({
		
	});
	
	window.DashboardView = Backbone.View.extend({
		
		tagName: 'section',
		className: 'dashboard',
		
		initialize: function() {
			_.bindAll(this, 'render');
			this.template = _.template($('#dashboard-template').html());
			this.collection.bind('reset', this.render);
		},
	
		render: function() {
			var $nagios_servers, 
				collection = this.collection;
			$(this.el).html(this.template({}));
			$nagios_servers = this.$('.nagios-servers');
			collection.each(function(nagios_server){
				var view = new DashboardNagiosServerView({
					model: nagios_server,
					collection: collection
				});
				$nagios_servers.append(view.render().el);
			});
			return this;
		}
		
		
	});
	
	window.NaggregatorRouter = Backbone.Router.extend({
		
		routes: {
			'':'home'
		},
		
		initialize: function(){
			this.dashboardView = new DashboardView({
				collection: window.library
			});
			
		},
		
		home: function() {
            $('#container').empty();
            $("#container").append(this.dashboardView.render().el);
		}
		
	});
	
	$(function(){
		window.App = new NaggregatorRouter();
		Backbone.history.start();
	});
	
})(jQuery);