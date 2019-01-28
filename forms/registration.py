from django import forms
from django.forms import ModelForm

from continuing_education.models.admission import Admission
from continuing_education.models.enums.enums import YES_NO_CHOICES


class RegistrationForm(ModelForm):
    previous_ucl_registration = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=YES_NO_CHOICES
    )

    class Meta:
        model = Admission
        fields = [
            # Professional Background
            'registration_type',
            'use_address_for_billing',
            'billing_address',
            'head_office_name',
            'company_number',
            'vat_number',
            'national_registry_number',
            'id_card_number',
            'passport_number',
            'marital_status',
            'spouse_name',
            'children_number',
            'previous_ucl_registration',
            'previous_noma',
            'use_address_for_post',
            'residence_address',
            'residence_phone',
            'registration_complete',
            'noma',
            'payment_complete',
            'formation_spreading',
            'prior_experience_validation',
            'assessment_presented',
            'assessment_succeeded',
            'sessions'
        ]


class StrictRegistrationForm(RegistrationForm):
    def __init__(self, data, **kwargs):
        super().__init__(data, **kwargs)

        required_fields = [
            'registration_type',
            'national_registry_number',
            'id_card_number',
            'marital_status',
            'previous_ucl_registration',
        ]

        for required_field in required_fields:
            self.fields[required_field].required = True
