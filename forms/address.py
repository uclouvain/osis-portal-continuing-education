import unicodedata

from dal import autocomplete
from django import forms
from django.utils.translation import gettext_lazy as _

from continuing_education.services.reference import CitiesService

BELGIUM_ISO_CODE = "BE"


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
        label=_("City")
    )

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('country') == BELGIUM_ISO_CODE:
            if cleaned_data.get('postal_code') and cleaned_data.get('city'):
                api_results = CitiesService.get_cities(
                    person=self.person,
                    zip_code=cleaned_data.get('postal_code'),
                )
                cities = api_results.get('results')

                if cities:
                    if not are_postal_code_and_city_compatible(cities, cleaned_data.get('city').lower()):
                        self.add_error('postal_code',
                                       _('Cities available for this belgian postal code %(postal_code)s are : '
                                         '%(possible_cities)s') % {
                                           'postal_code': str(cleaned_data.get('postal_code')),
                                           'possible_cities': ', '.join(city.name for city in cities),
                                       })

                else:
                    self.add_error('postal_code',
                                   _('Postal code (%(postal_code)s) not found in Belgium') % {
                                       'postal_code': str(cleaned_data.get('postal_code'))
                                   }
                                   )
        return cleaned_data

    def __init__(self, *args, person=None, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        self.person = person

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


def are_postal_code_and_city_compatible(cities, city_encoded) -> bool:
    for city in cities:
        city_name = city.name.lower()
        if city_name == city_encoded or \
                unicodedata.normalize('NFKD', city_name).encode('ascii', 'ignore') == \
                unicodedata.normalize('NFKD', city_encoded).encode('ascii', 'ignore'):
            return True
    return False
