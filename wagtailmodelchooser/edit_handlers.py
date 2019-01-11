from django.core import signing
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from wagtail.admin.edit_handlers import BaseChooserPanel, get_form_for_model

from .widgets import AdminModelChooser
from . import registry, Chooser

FILTERS = {}


class ModelChooserPanel(BaseChooserPanel, Chooser):
    model = None
    field_name = None
    filter_name = None
    auto_register = False
    show_add_link = False
    show_edit_link = False

    # Change the modal chooser template
    chooser_template = None

    # Key used to store this chooser in the registry
    chooser_id = None

    def __init__(self, field_name, filter_name=None, **kwargs):
        super().__init__(field_name, **kwargs)
        self.filter_name = filter_name
        if filter_name is not None:
            FILTERS[filter_name] = filter

    def on_instance_bound(self):
        """ Use the registry as a temporary cache to hold the chooser
        with it's instance. This works since the panel is cloned each
        time it's bound to an instance.

        """
        field = self.form.fields[self.field_name]
        if self.auto_register:
            chooser_id = self.get_chooser_id()
            if not chooser_id:
                raise ImproperlyConfigured(
                    "get_chooser_id must return a unique value")

            if chooser_id not in registry.choosers:
                registry.choosers[chooser_id] = self

            # Create data that can be used by the chooser view
            ctx = self.get_chooser_context()
            ctx['chooser_id'] = chooser_id
            field.widget.signed_data = signing.dumps(ctx, compress=True)

        if self.chooser_template:
            field.widget.chooser_template = self.chooser_template

        super().on_instance_bound()

    def widget_overrides(self):
        return {self.field_name: AdminModelChooser(
            model=self.target_model, filter_name=self.filter_name,
            show_edit_link=self.show_edit_link)}

    @property
    def target_model(self):
        return self.model._meta.get_field(self.field_name).remote_field.model

    def render_as_field(self):
        instance_obj = self.get_chosen_item()
        return mark_safe(render_to_string(self.field_template, {
            'field': self.bound_field,
            'instance': instance_obj,
        }))

    def get_chooser_id(self):
        """ Generate a key to use to store this chooser in the registry.
        By default it uses the fully qualified class name.
        """
        if self.chooser_id:
            return self.chooser_id
        cls = self.__class__
        return '%s.%s' % (cls.__module__, cls.__name__)

    def get_chooser_context(self):
        """ Generate data that can be used by the chooser view to
        re-populate the original panel information on the other side.

        This is called after the panel has been bound to a model and instance.
        """
        return {
            'field_name': self.field_name,
            'instance_pk': self.instance.pk,
            'app_label': self.model._meta.app_label,
            'model_name': self.model._meta.model_name,
        }

    def get_queryset(self, request):
        """ Get the queryset for the chooser. Override this as necessary.

        `model` is the  original model this panel was bound to and
        `target_model` is the model of the field being chosen.

        """
        return self.target_model._default_manager.all()

    def get_instance(self, request, panel_data):
        """ Get the original instance for the chooser.

        """
        return self.model._default_manager.get(pk=panel_data['instance_pk'])

    def get_form_class(self):
        return get_form_for_model(self.model,
                                  fields=self.required_fields(),
                                  widgets=self.widget_overrides())
