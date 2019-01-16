from django.core import signing
from django.shortcuts import reverse
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
    link_to_add_url = None
    link_to_edit_url = None

    # Change the modal chooser template
    chooser_template = None

    # Key used to store this chooser in the registry
    chooser_id = None

    def __init__(self, field_name, filter_name=None, auto_register=None,
                 show_add_link=None, show_edit_link=None,
                 link_to_add_url=None, link_to_edit_url=None, **kwargs):
        super().__init__(field_name, **kwargs)
        self.filter_name = filter_name
        if filter_name is not None:
            FILTERS[filter_name] = filter
        if auto_register is not None:
            self.auto_register = auto_register
        if show_add_link is not None:
            self.show_add_link = show_add_link
        if show_edit_link is not None:
            self.show_edit_link = show_edit_link
        if link_to_add_url is not None:
            self.link_to_add_url = link_to_add_url
        if link_to_edit_url is not None:
            self.link_to_edit_url = link_to_edit_url

    def clone(self):
        return self.__class__(
            field_name=self.field_name,
            filter_name=self.field_name,
            widget=self.widget if hasattr(self, 'widget') else None,
            heading=self.heading,
            classname=self.classname,
            help_text=self.help_text,
            auto_register=self.auto_register,
            show_add_link=self.show_add_link,
            show_edit_link=self.show_edit_link,
            link_to_add_url=self.link_to_add_url,
            link_to_edit_url=self.link_to_edit_url,
        )

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
            link_to_add_url=self.get_link_to_add_url(),
            link_to_edit_url=self.get_link_to_edit_url(),
            show_add_link=self.show_add_link,
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
        """ Get the original instance for the chooser or create an empty
        model if no pk is given.

        """
        pk = panel_data['instance_pk']
        if pk is not None:
            return self.model._default_manager.get(pk=pk)
        return self.model()

    def get_form_class(self):
        return get_form_for_model(self.model,
                                  fields=self.required_fields(),
                                  widgets=self.widget_overrides())

    def get_link_to_add_url(self):
        if self.link_to_add_url:
            return self.link_to_add_url
        opts = self.target_model._meta
        url_name = '{opts.app_label}_{opts.model_name}_modeladmin_create'
        return url_name.format(opts=opts)

    def get_link_to_edit_url(self):
        if self.link_to_edit_url:
            return self.link_to_edit_url
        opts = self.target_model._meta
        url_name = '{opts.app_label}_{opts.model_name}_modeladmin_edit'
        return url_name.format(opts=opts)
