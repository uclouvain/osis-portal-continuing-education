from django import forms
from django.forms import ModelForm, ChoiceField
from django.utils.translation import ugettext_lazy as _

from continuing_education.models.admission import Admission
from continuing_education.models.continuing_education_training import ContinuingEducationTraining
from continuing_education.models.enums import enums, admission_state_choices
from reference.models.country import Country


class AdmissionForm(ModelForm):
    formation = forms.ModelChoiceField(
        queryset=ContinuingEducationTraining.objects.filter(active=True).select_related('education_group')
    )
    state = ChoiceField(choices=admission_state_choices.STUDENT_STATE_CHOICES, required=False)
    citizenship = forms.ModelChoiceField(
        queryset=Country.objects.all().order_by('name'),
        label=_("Citizenship"),
        required=False,
    )
    high_school_diploma = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        required=False,
        choices=enums.YES_NO_CHOICES,
        label=_("High school diploma")
    )

    def __init__(self, data, **kwargs):
        formation = kwargs.pop('formation', None)
        super().__init__(data, **kwargs)
        if formation:
            self.initial['formation'] = formation
        qs = self.fields['formation'].queryset
        self.fields['formation'].queryset = qs.order_by(
            'education_group__educationgroupyear__acronym'
        ).distinct()

    class Meta:
        model = Admission
        fields = [
            'formation',

            # Contact
            'person_information',
            'citizenship',
            'address',
            'residence_phone',
            'phone_mobile',
            'email',

            # Education
            'high_school_diploma',
            'high_school_graduation_year',
            'last_degree_level',
            'last_degree_field',
            'last_degree_institution',
            'last_degree_graduation_year',
            'other_educational_background',

            # Professional Background
            'professional_status',
            'current_occupation',
            'current_employer',
            'activity_sector',
            'past_professional_activities',

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
            'awareness_other',

            # State
            'state',
        ]


class StrictAdmissionForm(AdmissionForm):
    def __init__(self, data, **kwargs):
        super().__init__(data, **kwargs)

        required_fields = [
            'citizenship',
            'phone_mobile',
            'email',
            'high_school_diploma',
            'last_degree_level',
            'last_degree_field',
            'last_degree_institution',
            'last_degree_graduation_year',
            'professional_status',
            'current_occupation',
            'current_employer',
            'activity_sector',
            'motivation',
            'professional_impact',
            'formation',
        ]

        for required_field in required_fields:
            self.fields[required_field].required = True
