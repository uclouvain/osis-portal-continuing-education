from datetime import datetime

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.backends import UserModel
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from base.views import layout
from base.views.layout import render
from osis_common.messaging import message_config, send_message as message_service
from django.forms import ModelForm
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _

from continuing_education.models.continuing_education_person import ContinuingEducationPerson
from reference.models.country import Country


class ContinuingEducationPersonForm(ModelForm):
    birth_country = forms.ModelChoiceField(
        queryset=Country.objects.all().order_by('name'),
        label=_("birth_country"),
        required=True,
    )

    birth_date = forms.DateField(
        widget=forms.SelectDateWidget(years=range(1900, datetime.now().year)),
        label=_("birth_date"),
        required=True
    )

    birth_location = forms.CharField(
        required=True,
        label=_("birth_location")
    )

    def __init__(self, *args, **kwargs):

        super(ContinuingEducationPersonForm, self).__init__(*args, **kwargs)

        if self.instance.pk:
            self._disable_existing_person_fields()

    def _disable_existing_person_fields(self):
        fields_to_disable = ["birth_country", "birth_date"]

        for field in self.fields.keys():
            self.fields[field].initial = getattr(self.instance, field)
            self.fields[field].widget.attrs['readonly'] = True
            if field in fields_to_disable:
                self.fields[field].widget.attrs['disabled'] = True

    class Meta:
        model = ContinuingEducationPerson
        fields = [
            'birth_date',
            'birth_location',
            'birth_country',
        ]


class ContinuingEducationPasswordResetForm(forms.Form):
    email = forms.EmailField(label=_("Email"), max_length=254)

    html_template_ref = 'continuing_education_password_reset_html'
    txt_template_ref = 'continuing_education_password_reset_txt'

    def save(self, token_generator=default_token_generator, request=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        email = self.cleaned_data["email"]
        try:
            user = User.objects.get(username=email)
        except (ObjectDoesNotExist, MultipleObjectsReturned) :
            error_message = _('This email does not exist in our database: {}').format(email)
        else:
            scheme = 'https' if request.is_secure() else 'http'
            site = get_current_site(request)
            url = reverse('password_reset_confirm', kwargs={'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                                                            'token': token_generator.make_token(user)})
            change_password_url = '{scheme}://{site}{url}'.format(scheme=scheme,
                                                                  site=site,
                                                                  url=url)
            error_message = self.send_password_reset_email(user, change_password_url)
        return error_message

    def send_password_reset_email(self, user, change_password_url):
        """
        Send the change password email.
        """
        receivers = [message_config.create_receiver(user.id, user.email, None)]
        template_base_data = {
            'change_password_url': change_password_url,

        }
        message_content = message_config.create_message_content(self.html_template_ref, self.txt_template_ref,
                                                                [], receivers, template_base_data, None)
        return message_service.send_messages(message_content,
                                             settings.IUFC_CONFIG.get('PASSWORD_RESET_MESSAGES_OUTSIDE_PRODUCTION'))



