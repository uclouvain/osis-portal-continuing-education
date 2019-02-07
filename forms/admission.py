from django import forms
from django.forms import Form
from django.utils.translation import ugettext_lazy as _

from base.models.academic_year import current_academic_year
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_categories
from continuing_education.models.address import Address
from continuing_education.models.continuing_education_person import ContinuingEducationPerson
from continuing_education.models.enums import enums, admission_state_choices
from reference.models.country import Country


class FormationChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, formation):
        return "{} {}".format(
            formation.acronym,
            formation.academic_year,
        )


class AdmissionForm(Form):
    formation = FormationChoiceField(queryset=EducationGroupYear.objects.all())
    state = forms.ChoiceField(choices=admission_state_choices.STUDENT_STATE_CHOICES, required=False)
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

    person_information = forms.ModelChoiceField(
        queryset=ContinuingEducationPerson.objects.all(),
        required=False,
        label=_("Person information")
    )

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

        qs = EducationGroupYear.objects.filter(education_group_type__category=education_group_categories.TRAINING)

        curr_academic_year = current_academic_year()
        next_academic_year = curr_academic_year.next() if curr_academic_year else None

        if next_academic_year:
            qs = qs.filter(academic_year=next_academic_year).order_by('acronym')
        else:
            qs = qs.order_by('acronym', 'academic_year__year')

        self.fields['formation'].queryset = qs


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
