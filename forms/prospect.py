from dal import autocomplete
from django import forms
from django.forms import Form
from django.utils.translation import gettext_lazy as _


class ProspectForm(Form):
    first_name = forms.CharField(
        required=True,
        label=_("First name"),
        max_length=20,
    )

    name = forms.CharField(
        required=True,
        label=_("Name"),
        max_length=40,
    )

    postal_code = forms.CharField(
        required=True,
        label=_("Postal code")
    )

    city = forms.CharField(
        required=True,
        label=_("City")
    )

    email = forms.EmailField(
        required=True,
        label=_("Email")
    )

    phone_number = forms.CharField(
        required=True,
        label=_("Phone number")
    )

    formation = autocomplete.Select2ListCreateChoiceField(
        widget=autocomplete.ListSelect2(url='cetraining-autocomplete'),
        required=True,
        label=_("Formation")
    )

    def __init__(self, *args, **kwargs):
        formation = kwargs.pop('ce_training', None)
        super(ProspectForm, self).__init__(*args, **kwargs)
        if formation:
            self.fields['formation'] = forms.CharField(
                disabled=True
            )
            self.initial['formation'] = formation['education_group']['acronym']

    class Meta:
        fields = [
            'name',
            'first_name',
            'postal_code',
            'city',
            'email',
            'phone_number',
            'formation',
        ]
