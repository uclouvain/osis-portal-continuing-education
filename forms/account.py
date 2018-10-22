from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from continuing_education.models.continuing_education_person import ContinuingEducationPerson

from reference.models.country import Country


class ContinuingEducationPersonForm(ModelForm):
    birth_country = forms.ModelChoiceField(
        queryset=Country.objects.all().order_by('name'),
        label=_("birth_country"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        b_date = kwargs.pop('b_date', None)
        b_location = kwargs.pop('b_location', None)
        b_country = kwargs.pop('b_country', None)

        super(ContinuingEducationPersonForm, self).__init__(*args, **kwargs)
        if b_date:
            self.fields['birth_date'].initial = b_date
        if b_location:
            self.fields['birth_location'].initial = b_location
            self.fields['birth_location'].widget.attrs['readonly'] = True
        if b_country:
            self.fields['birth_country'].initial = b_country
            self.fields['birth_country'].widget.attrs['disabled'] = True

    def clean_birth_country(self):
        if self.instance:
            return self.instance.birth_country
        else:
            return self.fields['birth_country']

    class Meta:
        model = ContinuingEducationPerson
        fields = [
            'birth_date',
            'birth_location',
            'birth_country',
        ]
