from django.forms import ModelForm

from continuing_education.models.address import Address


class AddressForm(ModelForm):

    class Meta:
        model = Address
        fields = [
            'location',
            'postal_code',
            'city',
            'country'
        ]
