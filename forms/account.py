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

        super(ContinuingEducationPersonForm, self).__init__(*args, **kwargs)

        if self.instance.pk:
            self._disable_existing_person_fields()

    def _disable_existing_person_fields(self):
        for field in self.fields.keys():
            self.fields[field].initial = getattr(self.instance, field)
            self.fields[field].widget.attrs['readonly'] = True
            if field is "birth_country":
                self.fields[field].widget.attrs['disabled'] = True

    def clean_birth_country(self):
        if self.instance.birth_country:
            return self.instance.birth_country
        else:
            b_country = self.cleaned_data['birth_country']
            return Country.objects.filter(name=b_country).first()

    class Meta:
        model = ContinuingEducationPerson
        fields = [
            'birth_date',
            'birth_location',
            'birth_country',
        ]
