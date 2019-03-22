from dal import autocomplete
from django import forms
from django.forms import ChoiceField, Form
from django.utils.translation import gettext_lazy as _

from continuing_education.models.enums import enums, admission_state_choices


class AdmissionForm(Form):

    formation = autocomplete.Select2ListCreateChoiceField(
        widget=autocomplete.ListSelect2(url='cetraining-autocomplete'),
        required=True,
    )

    state = ChoiceField(
        choices=admission_state_choices.STUDENT_STATE_CHOICES,
        required=False
    )
    citizenship = autocomplete.Select2ListCreateChoiceField(
        widget=autocomplete.ListSelect2(url='country-autocomplete'),
        required=False,
    )
    high_school_diploma = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        required=False,
        choices=enums.YES_NO_CHOICES,
        label=_("High school diploma")
    )

    person_information = forms.CharField(
        required=False,
    )

    # Contact
    address = forms.CharField(
        required=False,
    )
    phone_mobile = forms.CharField(
        max_length=50,
        required=False,
        label=_("Phone mobile")
    )
    email = forms.EmailField(
        max_length=255,
        required=False,
        label=_("Additional email")
    )

    # Education

    high_school_graduation_year = forms.IntegerField(
        required=False,
        label=_("High school graduation year")
    )
    last_degree_level = forms.CharField(
        max_length=50,
        required=False,
        label=_("Last degree level")
    )
    last_degree_field = forms.CharField(
        max_length=50,
        required=False,
        label=_("Last degree field")
    )
    last_degree_institution = forms.CharField(
        max_length=50,
        required=False,
        label=_("Last degree institution")
    )
    last_degree_graduation_year = forms.IntegerField(
        required=False,
        label=_("Last degree graduation year")
    )
    other_educational_background = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label=_("Other educational background")
    )

    # Professional Background
    professional_status = forms.ChoiceField(
        required=False,
        choices=enums.STATUS_CHOICES,
        label=_("Professional status")
    )
    current_occupation = forms.CharField(
        max_length=50,
        required=False,
        label=_("Current occupation")
    )
    current_employer = forms.CharField(
        max_length=50,
        required=False,
        label=_("Current employer")
    )
    activity_sector = forms.ChoiceField(
        required=False,
        choices=enums.SECTOR_CHOICES,
        label=_("Activity sector")
    )
    past_professional_activities = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label=_("Past professional activities")
    )

    # Motivation
    motivation = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label=_("Motivation")
    )
    professional_impact = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label=_("Professional impact")
    )

    # Awareness
    awareness_ucl_website = forms.BooleanField(
        initial=False,
        required=False,
        label=_("Awareness UCL website")
    )
    awareness_formation_website = forms.BooleanField(
        initial=False,
        required=False,
        label=_("Awareness formation website")
    )
    awareness_press = forms.BooleanField(
        initial=False,
        required=False,
        label=_("Awareness press")
    )
    awareness_facebook = forms.BooleanField(
        initial=False,
        required=False,
        label=_("Awareness Facebook")
    )
    awareness_linkedin = forms.BooleanField(
        initial=False,
        required=False,
        label=_("Awareness LinkedIn")
    )
    awareness_customized_mail = forms.BooleanField(
        initial=False,
        required=False,
        label=_("Awareness customized mail")
    )
    awareness_emailing = forms.BooleanField(
        initial=False,
        required=False,
        label=_("Awareness emailing")
    )
    awareness_other = forms.CharField(
        max_length=100,
        required=False,
        label=_("Awareness other")
    )

    # State

    state_reason = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label=_("State reason")
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        formation = kwargs.pop('formation', None)
        super(AdmissionForm, self).__init__(*args, **kwargs)
        if formation:
            self.initial['formation'] = (formation['uuid'], formation['education_group']['acronym'])
            self.fields['formation'].choices = [self.initial['formation']]
        if self.instance:
            self._set_initial_fields()

    def _set_initial_fields(self):
        fields_to_set = [('citizenship', 'name', 'iso_code'), ('formation', 'acronym', 'uuid')]
        for field, attribute, slug in fields_to_set:
            if self.instance[field]:
                self.instance[field] = (
                    self.instance[field][slug],
                    self.instance[field]['education_group'][attribute]
                    if field == 'formation' else self.instance[field][attribute]
                )
                self.fields[field].choices = [self.instance[field]]
        self.initial = self.instance


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
