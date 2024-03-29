from datetime import datetime

from dal import autocomplete
from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _
from django_registration.forms import RegistrationFormUniqueEmail

from osis_common.messaging import message_config, send_message as message_service


class ContinuingEducationPersonForm(forms.Form):
    birth_country = autocomplete.Select2ListCreateChoiceField(
        widget=autocomplete.ListSelect2(url='country-autocomplete'),
        required=True,
        label=_("Birth country")
    )

    birth_date = forms.DateField(
        widget=forms.SelectDateWidget(years=range(1900, datetime.now().year)),
        label=_("Birth date"),
        required=True
    )

    birth_location = forms.CharField(
        required=True,
        label=_("Birth location")
    )

    def __init__(self, *args, **kwargs):
        super(ContinuingEducationPersonForm, self).__init__(*args, **kwargs)
        if self.initial:
            self.initial['birth_country'] = (
                self.initial['birth_country']['iso_code'],
                self.initial['birth_country']['name']
            )
            self._disable_existing_person_fields()

    def _disable_existing_person_fields(self):
        fields_to_disable = ["birth_country", "birth_date"]
        for field in self.fields.keys():
            if field == 'birth_country':
                self.fields[field].choices = [self.initial[field]]
            self.fields[field].widget.attrs['readonly'] = True

            if field in fields_to_disable:
                self.fields[field].widget.attrs['disabled'] = True


class ContinuingEducationPasswordResetForm(forms.Form):
    email = forms.EmailField(label=_("Email"), max_length=254)

    html_template_ref = 'continuing_education_password_reset_html'
    txt_template_ref = 'continuing_education_password_reset_txt'

    def save(self, token_generator=default_token_generator, request=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user
        """
        email = self.cleaned_data["email"]
        try:
            user = User.objects.get(username=email)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            error_message = _('This email does not exist in our database: %(mail)s') % {"mail": email}
        else:
            scheme = 'https' if request.is_secure() else 'http'
            site = get_current_site(request)
            url = reverse('password_reset_confirm', kwargs={
                'uidb64': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': token_generator.make_token(user)
            })
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


def email_not_from_uclouvain(email):
    if email.endswith('uclouvain.be'):
        raise ValidationError(_("Please use an email address not ending with uclouvain.be to create your account."))


class ContinuingEducationRegistrationForm(RegistrationFormUniqueEmail):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        email_field = User.get_email_field_name()
        self.fields[email_field].validators.append(email_not_from_uclouvain)


class ContinuingEducationAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username_field.verbose_name = User.get_email_field_name()
