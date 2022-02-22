from dal import autocomplete
from django import forms
from django.utils.translation import gettext_lazy as _


class AddressForm(forms.Form):
    country = autocomplete.Select2ListCreateChoiceField(
        widget=autocomplete.ListSelect2(url='country-autocomplete'),
        required=False,
        label=_("Country")
    )

    location = forms.CharField(
        max_length=50,
        required=False,
        label=_("Location")
    )
    postal_code = forms.CharField(
        max_length=12,
        required=False,
        label=_("Postal code")
    )
    city = forms.CharField(
        max_length=40,
        required=False,
        label=_("Cityy")
    )

    def __init__(self, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        if self.initial and self.initial['country']:
            self.initial['country'] = (self.initial['country']['iso_code'], self.initial['country']['name'])
            self.fields['country'].choices = [self.initial['country']]


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
