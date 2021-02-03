from django import forms
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from continuing_education.forms.admission import phone_regex
from continuing_education.models.enums import enums
from continuing_education.models.enums.enums import YES_NO_CHOICES
from osis_common.utils.validators import belgium_national_register_number_validator

alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', _('Only alphanumeric characters are allowed.'))
numeric = RegexValidator(r'^[0-9]*$', _('Only numeric characters are allowed.'))


class RegistrationForm(forms.Form):
    previous_ucl_registration = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=YES_NO_CHOICES
    )
    # Billing
    registration_type = forms.ChoiceField(
        required=False,
        choices=enums.REGISTRATION_TITLE_CHOICES,
        label=_("Registration type")
    )
    use_address_for_billing = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=[
            (True, _("residence address mentioned earlier")),
            (False, _("an other address"))
        ],
        label=_('I would like the billing address to be :'),
        required=False
    )
    billing_address = forms.CharField(
        required=False,
        label=_("Billing address")
    )
    head_office_name = forms.CharField(
        max_length=255,
        required=False,
        label=_("Head office name")
    )
    company_number = forms.CharField(
        max_length=255,
        required=False,
        label=_("Company number")
    )
    vat_number = forms.CharField(
        max_length=255,
        required=False,
        label=_("VAT number")
    )

    national_registry_number = forms.CharField(
        max_length=255,
        required=False,
        label=_("National registry number"),
        validators=[numeric, belgium_national_register_number_validator]
    )
    id_card_number = forms.CharField(
        max_length=255,
        required=False,
        label=_("ID card number"),
        validators=[alphanumeric]
    )
    passport_number = forms.CharField(
        max_length=255,
        required=False,
        label=_("Passport number"),
        validators=[alphanumeric]
    )
    marital_status = forms.ChoiceField(
        required=False,
        choices=enums.MARITAL_STATUS_CHOICES,
        label=_("Marital status")
    )
    spouse_name = forms.CharField(
        max_length=255,
        required=False,
        label=_("Spouse name")
    )
    children_number = forms.IntegerField(
        required=False,
        initial=0,
        label=_("Children number")
    )

    previous_noma = forms.CharField(
        max_length=255,
        required=False,
        label=_("Previous NOMA")
    )

    # Post
    use_address_for_post = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=[
            (True, _("residence address mentioned earlier")),
            (False, _("an other address"))
        ],
        label=_('I would like the post address to be :'),
        required=False
    )
    residence_address = forms.CharField(
        required=False,
        label=_("Residence address")
    )

    residence_phone = forms.CharField(
        max_length=50,
        required=False,
        label=_("Residence phone")
    )

    def clean_residence_phone(self):
        return self.cleaned_data['residence_phone'].replace(' ', '')

    def __init__(self, data, only_billing=False, **kwargs):
        super().__init__(data, **kwargs)
        if only_billing:
            self.fields['previous_ucl_registration'].required = False


class StrictRegistrationForm(RegistrationForm):
    residence_phone = forms.CharField(
        validators=[phone_regex],
        required=False,
        label=_("Residence phone"),
        widget=forms.TextInput(attrs={'placeholder': '082123456 - 003282123456 - +3282123456'})
    )

    def __init__(self, data, **kwargs):
        super().__init__(data, **kwargs)

        required_fields = [
            'registration_type',
            'marital_status',
            'previous_ucl_registration',
        ]

        for required_field in required_fields:
            self.fields[required_field].required = True

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('national_registry_number') and \
                not cleaned_data.get('id_card_number') and \
                not cleaned_data.get('passport_number'):
            self.add_error('national_registry_number', 'national_registry_number')

        return cleaned_data
