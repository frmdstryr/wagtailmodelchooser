import json

from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from wagtail.admin.widgets import AdminChooser


class AdminModelChooser(AdminChooser):
    signed_data = None
    chooser_template = "wagtailmodelchooser/model_chooser.html"

    def __init__(self, model, filter_name=None, **kwargs):
        self.target_model = model
        name = self.target_model._meta.verbose_name
        self.choose_one_text = _('Choose %s') % name
        self.choose_another_text = _('Choose another')
        self.filter_name = filter_name
        self.link_to_chosen_text = kwargs.pop('link_to_chosen_text', _('Edit'))
        self.link_to_add_text = kwargs.pop('link_to_add_text ', _('Add'))
        self.link_to_edit_url = kwargs.pop('link_to_edit_url', '#')
        self.link_to_add_url = kwargs.pop('link_to_add_url', '#')
        self.show_edit_link = kwargs.get(
            'show_edit_link', False) and (self.link_to_edit_url != '#')
        self.show_add_link = kwargs.pop(
            'show_add_link', False) and (self.link_to_add_url != '#')

        super(AdminModelChooser, self).__init__(**kwargs)

    def render_html(self, name, value, attrs):
        instance, value = self.get_instance_and_id(self.target_model, value)
        original_field_html = super(AdminModelChooser, self).render_html(
            name, value, attrs)

        return render_to_string(self.chooser_template, {
            'widget': self,
            'model_opts': self.target_model._meta,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'item': instance,
        })

    def render_js_init(self, id_, name, value):
        opts = self.target_model._meta
        kwargs = {'app_label': opts.app_label, 'model_name': opts.model_name}
        if self.filter_name:
            kwargs['filter_name'] = self.filter_name
        if self.signed_data:
            kwargs = {'signed_data': self.signed_data}

        return "createModelChooser({id}, {url});".format(
            id=json.dumps(id_),
            url=json.dumps(reverse('model_chooser', kwargs=kwargs)),
            filter_name=json.dumps(self.filter_name))
