
DefaultFormInterface = {
  container: function (name) {
    return $(name+'-container');
  },
  control: function (name) {
    return $(name+'-control');
  }
}

var FieldAPI = Class.create();
FieldAPI.prototype = {
  initialize: function (eventapi) {
    this.eventapi = eventapi;
  },
  extractValue: function (field_name) {
    return Form.serialize(this.eventapi.form.container(field_name));
  }
}

var EventAPI = Class.create();
EventAPI.prototype = {
  initialize: function(url, parameters, forminterface) {
    this.url = url;
    this.form = forminterface || DefaultFormInterface;
    this.fields = new FieldAPI(this);
    this.options = $H({
	method: 'post',
	onSuccess: this._handleSuccess,
	onFailure: this._handleFailure,
	parameters: parameters || {}});
  },

  sendEvent: function(eventName, values) {
    options = this.options;
    params = $H(options.parameters || {});
    params = params.merge($H({event: eventName}));
    query_strings = $A(values);
    query_strings.push(params.toQueryString());
    options = options.merge({parameters: query_strings.join('&')});
    var r = new Ajax.Request(this.url, options);
  },

  _handleSuccess: function(request) {
    eval(request.responseText);
  },
  
  _handleFailure: function() {
    alert('handleFailure');
  }
}
