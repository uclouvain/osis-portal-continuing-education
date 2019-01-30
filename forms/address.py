from django import forms
from django.forms import Form
from django.utils.translation import ugettext_lazy as _

from reference.models.country import Country


class AddressForm(Form):
    country = forms.ModelChoiceField(
        queryset=Country.objects.all().order_by('name'),
        label=_("Country"),
        required=False,
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
