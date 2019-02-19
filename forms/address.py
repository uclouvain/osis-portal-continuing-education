from dal import autocomplete
from django import forms
from django.utils.translation import ugettext_lazy as _

from base.views.autocomplete.common import get_country_list_from_osis


class AddressForm(forms.Form):
    country = autocomplete.Select2ListChoiceField(
        choice_list=get_country_list_from_osis,
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
