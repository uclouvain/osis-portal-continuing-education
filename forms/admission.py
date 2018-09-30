from django import forms
from django.forms import ModelForm, ChoiceField

from continuing_education.models.admission import Admission
from continuing_education.views.home import fetch_example_data


class TitleChoiceField(forms.ModelChoiceField):
    def label_from_instance(obj):
        return "{} - {}".format(obj.acronym, obj.title)

class AdmissionForm(ModelForm):
    sorted_formations = sorted(fetch_example_data(), key=lambda k: k['acronym'])
    FORMATION_CHOICES = tuple([(x['acronym'], " - ".join([x['acronym'], x['title']]))
                               for x in sorted_formations])

    formation = ChoiceField(choices=FORMATION_CHOICES)

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
