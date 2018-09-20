from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from continuing_education.models.continuing_education_person import ContinuingEducationPerson


class ContinuingEducationPersonForm(ModelForm):

    class Meta:
        model = ContinuingEducationPerson
        fields = [
            'birth_location',
            'birth_country',
            'city',
            'location',
            'postal_code',
            'country'
        ]
        labels = {field: _(field) for field in fields}
