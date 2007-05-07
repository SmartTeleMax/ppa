
"""
PPA Forms package.

Usage:

1. Importing

from PPA.UI.Forms import Form, Converters, Fields

2. Defining fields

PPA.UI.Forms provides a number of prepared, preconfigured fields, all of them
are located in Fields module. To use field class - create an instance of it,
providing params as keyword arguments.

Any field may accept 'default' argument, it's field's default value, but it's
not ness. to provide it any time.

There are also a so-called ScalarFields, if field is represented in form by
ONE html control (like <input type='text'> of <textarea>) it is ScalarField.

ScalarFields may accept converter as 'converter' keyword argument. Converters
are defined in Converters module.

Example:

    string_field = String(default='Enter your name here')
    integer_field = Integer(default=100) # every field has defa
    email_field = String(converter=Converters.Email)

3. Defining a schema.

Fields collection is called a schema, is't represented by Fields.Schema class.
To define a schema create an instance of Fields.Schema, providing a keyword
argument 'subfields', a list of tuples of ('field_name', field_instance):

    user_schema = Fields.Schema(subfields=[
        ('name', Fields.String(title=u'Name', converter=Converters.NotNull)),
        ('email', Fields.String(title=u'E-mail', converter=Converters.Email)),
        ('passwd', Fields.Password(title=u'Password', converter=Converters.NotNull)),
        ])

3. Using Form object.

Form is a statefull form representation.

3.1. Form instantiation:

Form requires a fields specification, provided as Fields.Schema instance,
or just a list of subfields (as provided to Schema):

    form = Form(schema)

You may want to pass a default values to form:

    form = Form(schema, values=dict(email='Enter your email here'))

Or give some special application-specific data to be accessable in fields,
like a db-connector:

    form = Form(schema, params=dict(session=sqlalchemy.create_session(db)))

To render an empty form, use a render() emthod, in only accepts template_controller argument (an instance of PPA.Template.TemplateController). template_controller is used to find fields templates.

The result of render is dict of two keys, 'content' - rendered form html and 'requisited' (not documented yet).

    rendered_form = form.render(template_controller)

To accept and convert values use accept(), the only argument is PPA.HTTP.Form.Form instance:

    form.accept(field_storage)

After form is accepted you may use it next ways:

if form.hasErrors():
    errors = form.errors # dict of errors, keys are field names
else:
    accepted_values = form.value # dict of converted values, keys are field names, values are python objects returted by fields.

4. Field templates.

template_controller, given to render() is used to find templates for fields.
MRO is used to resolve template names. For example, if we have:

class Field: pass
class ScalarField: pass
class String(ScalarField): pass
class Email(String): pass

and Email instance tries to render template, templates are being searched using template controller in the next order:

'Email', 'String', 'ScalarField', 'Fields'

Refer to fields docstrings to determine template's namespaces.

Thats all.
"""

from Form import Form
import Converters, Fields, Layout
