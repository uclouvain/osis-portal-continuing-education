from dal import autocomplete
from django import forms
from django.core.validators import RegexValidator
from django.forms import ChoiceField, Form
from django.utils.translation import gettext_lazy as _

from continuing_education.models.enums import enums, admission_state_choices
from reference.models.country import Country

phone_regex = RegexValidator(
    regex=r'^(?P<prefix_intro>\+|0{1,2})\d{7,15}$',
    message=_("Phone number must start with 0 or 00 or '+' followed by at least 7 digits and up to 15 digits.")
)


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
        label=_("Citizenship")
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
        required=False,
        label=_("Phone mobile"),
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
    professional_personal_interests = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label=_("Professional and personal interests")
    )

    # Awareness
    awareness_ucl_website = forms.BooleanField(
        initial=False,
        required=False,
        label=_("By UCLouvain website")
    )
    awareness_formation_website = forms.BooleanField(
        initial=False,
        required=False,
        label=_("By formation website")
    )
    awareness_press = forms.BooleanField(
        initial=False,
        required=False,
        label=_("By press")
    )
    awareness_facebook = forms.BooleanField(
        initial=False,
        required=False,
        label=_("By Facebook")
    )
    awareness_linkedin = forms.BooleanField(
        initial=False,
        required=False,
        label=_("By LinkedIn")
    )
    awareness_customized_mail = forms.BooleanField(
        initial=False,
        required=False,
        label=_("By customized mail")
    )
    awareness_emailing = forms.BooleanField(
        initial=False,
        required=False,
        label=_("By emailing")
    )
    awareness_word_of_mouth = forms.BooleanField(
        initial=False,
        required=False,
        label=_("By word of mouth")
    )
    awareness_friends = forms.BooleanField(
        initial=False,
        required=False,
        label=_("By friends")
    )
    awareness_former_students = forms.BooleanField(
        initial=False,
        required=False,
        label=_("By former students")
    )
    awareness_moocs = forms.BooleanField(
        initial=False,
        required=False,
        label=_("By Moocs")
    )
    awareness_other = forms.CharField(
        max_length=100,
        required=False,
        label=_("Other")
    )

    # State
    state_reason = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label=_("State reason")
    )

    def clean_phone_mobile(self):
        return self.cleaned_data['phone_mobile'].replace(' ', '')

    def __init__(self, *args, **kwargs):
        formation = kwargs.pop('formation', None)
        super(AdmissionForm, self).__init__(*args, **kwargs)
        if formation:
            self.initial['formation'] = (formation['uuid'], formation['acronym'])
            self.fields['formation'].choices = [self.initial['formation']]
        elif self.initial:
            self._set_initial_fields()

    def _set_initial_fields(self):
        if self.initial.get('formation'):
            self.initial['formation'] = (
                self.initial['formation']['uuid'],
                self.initial['formation']['acronym']
            )
            self.fields['formation'].choices = [self.initial['formation']]
        if self.initial.get('citizenship'):
            self.initial['citizenship'] = (
                Country.objects.get(name=self.initial['citizenship']).iso_code,
                self.initial['citizenship']
            )
            self.fields['citizenship'].choices = [self.initial['citizenship']]


class StrictAdmissionForm(AdmissionForm):
    phone_mobile = forms.CharField(
        validators=[phone_regex],
        required=False,
        label=_("Phone mobile"),
        widget=forms.TextInput(attrs={'placeholder': '0474123456 - 0032474123456 - +32474123456'})
    )

    def __init__(self, data, **kwargs):
        super().__init__(data, **kwargs)

        required_fields = [
            'citizenship',
            'phone_mobile',
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
            'professional_personal_interests',
            'formation',
        ]

        for required_field in required_fields:
            self.fields[required_field].required = True
