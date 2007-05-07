
from Base import NVContext, FieldTemplateSelector
from Fields import Schema

class Form:

    # public parameters:
    #   schema          - form schema (either Schema object or list of fields)
    #   value           - converted (python) values
    #   filter          - access control filter
    #   params          - any object to pass to fields (application dependent)
    # for internal use:
    #   errors          - occured errors
    #   form_content    - None # original form params
    
    def __init__(self, schema, value=None, params=None,
                 errors=None, form_content=None):
        if not isinstance(schema, Schema):
            schema = Schema(subfields=schema)
        self.schema = schema
        self.params = params
        self.errors = errors or {}
        self.form_content = form_content or {}
        if value is None:
            value = schema.getDefault(self, NVContext())
        self.value = value

    def render(self, template_controller, global_namespace={}):
        """Renders form using template_controller to find fields templates,
        returns dict(content=unicode, requisites=list), where content is
        form rendered to html and requisites is SOMETHING"""
        context = NVContext(self.value)
        if not self.form_content:
            self.form_content = self.schema.toForm(self, context)
        requisites = self.createRequisites()
        template_selector = FieldTemplateSelector(
                                    template_controller.getTemplate)
        content = self.schema.render(self, context, requisites,
                                     template_selector, global_namespace)
        return {'content': content, 'requisites': requisites}

    def accept(self, form):
        """Accepts form fields from from (PPA.HTTP.Form) with self.schema,
        initialized something of self.errors, self.form_content, self.content
        """
        context = NVContext(self.value)
        # XXX Do we need to return form_content and errors or just fill them
        # in-place?
        self.value, self.errors = self.schema.accept(self, context, form)

    def hasErrors(self):
        return bool(self.errors)

    def event(self): # XXX what else?
        raise NotImplementedError()

    def createRequisites(self):
        return {}
