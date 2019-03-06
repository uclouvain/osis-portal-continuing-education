from dal import autocomplete
from django import forms
from django.utils.translation import ugettext_lazy as _


class AddressForm(forms.Form):
    country = autocomplete.Select2ListCreateChoiceField(
        widget=autocomplete.ListSelect2(url='country-autocomplete'),
        required=False
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

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super(AddressForm, self).__init__(*args, **kwargs)

        if self.instance:
            self.instance['country'] = self.instance['country']['name']
            self.fields['country'].choices = [(self.instance['country'], self.instance['country'])]
            self.initial = self.instance


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
