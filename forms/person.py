from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from base.models.person import Person

GENDER_CHOICES = (
    ('', '---------'),
    ('F', _('female')),
    ('H', _('male'))
)
HELP_MSG_FIRST_LETTER_UPPERCASE = _("Only the first letter uppercase.")


def _capitalize_choices(choices):
    return ((choice[0], choice[1].capitalize()) for choice in choices)


class PersonForm(ModelForm):
    first_name = forms.CharField(
        required=True,
        label=_("First name"),
        help_text=HELP_MSG_FIRST_LETTER_UPPERCASE,
        max_length=20,
    )

    last_name = forms.CharField(
        required=True,
        label=_("Last name"),
        help_text=HELP_MSG_FIRST_LETTER_UPPERCASE,
        max_length=40,
    )

    gender = forms.ChoiceField(
        choices=_capitalize_choices(GENDER_CHOICES),
        required=True,
        label=_("Gender")
    )

    def __init__(self, no_first_name_checked, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)
        if no_first_name_checked or self._has_no_first_name():
            self.fields['first_name'].required = False
        if self.instance.pk:
            self._disable_existing_person_fields()
            self._disable_first_name_field()
        self.fields['email'].label = _('Email')

    def _disable_existing_person_fields(self):
        for field in self.fields.keys():
            attr = getattr(self.instance, field)
            if attr and attr != 'X':
                self.fields[field].initial = attr
                self.fields[field].widget.attrs['readonly'] = True
                if field == "gender":
                    self.fields[field].widget.attrs['disabled'] = True

    def _disable_first_name_field(self):
        if self._has_no_first_name():
            self.fields['first_name'].required = False
            self.fields['first_name'].widget.attrs['readonly'] = True

    def _has_no_first_name(self):
        return getattr(self.instance, 'last_name') and not getattr(self.instance, 'first_name')

    class Meta:
        model = Person

        fields = [
            'first_name',
            'last_name',
            'email',
            'gender'
        ]


class StrictPersonForm(PersonForm):
    def __init__(self, data, **kwargs):
        super().__init__(data=data, no_first_name_checked=True, **kwargs)
