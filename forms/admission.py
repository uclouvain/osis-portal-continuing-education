import requests
from django import forms
from django.conf import settings
from django.forms import Form
from django.utils.translation import ugettext_lazy as _

from continuing_education.models.address import Address
from continuing_education.models.enums import enums, admission_state_choices
from continuing_education.views.common import transform_response_to_data, get_country_list_from_osis


class FormationChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, formation):
        return "{} {}".format(
            formation.acronym,
            formation.academic_year,
        )


class AdmissionForm(Form):
    def get_training_list_from_osis(self, filter_field=None, filter_value=None):
        header_to_get = {'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN}
        url = 'http://localhost:18000/api/v1/education_group/trainings/'
        if filter_field and filter_value:
            url = url + "?" + filter_field + "=" + filter_value
        response = requests.get(
            url=url,
            headers=header_to_get
        )
        return transform_response_to_data(response)

    formation = forms.CharField()
    state = forms.ChoiceField(choices=admission_state_choices.STUDENT_STATE_CHOICES, required=False)
    citizenship = forms.CharField()
    high_school_diploma = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        required=False,
        choices=enums.YES_NO_CHOICES,
        label=_("High school diploma")
    )

    person_information = forms.CharField()

    # Contact
    address = forms.ModelChoiceField(
        queryset=Address.objects.all(),
        required=False,
        label=_("Address")
    )
    phone_mobile = forms.CharField(
        max_length=30,
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

    def __init__(self, data, **kwargs):
        super().__init__(data, **kwargs)
        self.fields['citizenship'].choices = get_country_list_from_osis()
        self.fields['formation'].choices = self.get_training_list_from_osis()


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
