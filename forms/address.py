from dal import autocomplete
from django import forms
from django.forms import Form, ModelForm
from django.utils.translation import ugettext_lazy as _

from continuing_education.models.address import Address
from continuing_education.views.api import get_countries_list
from reference.models.country import Country


class AddressModelForm(ModelForm):
    country = forms.ModelChoiceField(
        queryset=Country.objects.all().order_by('name'),
        label=_("Country"),
        required=False,
    )

    class Meta:
        model = Address
        fields = [
            'location',
            'postal_code',
            'city',
            'country'
        ]


class AddressForm(Form):

    country = autocomplete.Select2ListChoiceField(
        choice_list=get_countries_list,
        widget=autocomplete.ListSelect2(url='country-autocomplete'),
    )

    location = forms.CharField(
        max_length=255,
        required=False,
        label=_("Location")
    )
    postal_code = forms.CharField(
        max_length=20,
        required=False,
        label=_("Postal code")
    )
    city = forms.CharField(
        max_length=255,
        required=False,
        label=_("City")
    )


class StrictAddressForm(AddressForm):
    def __init__(self, data, **kwargs):
        super().__init__(data, **kwargs)

        required_fields = [
            'location',
            'postal_code',
            'city',
            'country',
        ]

        for required_field in required_fields:
            self.fields[required_field].required = True


class StrictAddressModelForm(AddressModelForm):
    def __init__(self, data, **kwargs):
        super().__init__(data, **kwargs)

        required_fields = [
            'location',
            'postal_code',
            'city',
            'country',
        ]

        for required_field in required_fields:
            self.fields[required_field].required = True
