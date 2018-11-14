from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from continuing_education.models.address import Address
from reference.models.country import Country


class AddressForm(ModelForm):
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
