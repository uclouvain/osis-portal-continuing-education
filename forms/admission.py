from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm, ChoiceField
from django.utils.translation import ugettext_lazy as _

from continuing_education.models.admission import Admission
from continuing_education.models.enums.enums import STUDENT_STATE_CHOICES, get_enum_keys
from continuing_education.views.home import fetch_example_data


class TitleChoiceField(forms.ModelChoiceField):
    def label_from_instance(obj):
        return "{} - {}".format(obj.acronym, obj.title)


class AdmissionForm(ModelForm):
    FORMATION_CHOICES = tuple([(x['acronym'], " - ".join([x['acronym'], x['title']]))
                               for x in fetch_example_data()])

    formation = ChoiceField(choices=FORMATION_CHOICES)

    def clean(self):
        if self.cleaned_data['state'] not in get_enum_keys(STUDENT_STATE_CHOICES):
            raise ValidationError(_('invalid state'), code='invalid')

    class Meta:
        model = Admission
        fields = [
            'formation',
            'person_information',
            # Motivation
            'motivation',
            'professional_impact',
            # Awareness
            'awareness_ucl_website',
            'awareness_formation_website',
            'awareness_press',
            'awareness_facebook',
            'awareness_linkedin',
            'awareness_customized_mail',
            'awareness_emailing',
            # State
            'state',
        ]
