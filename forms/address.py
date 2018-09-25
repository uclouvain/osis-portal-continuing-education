from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

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
        #automatic translation of field names
        labels = {field : _(field) for field in fields}
