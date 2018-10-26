from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from base.models.person import Person


def _capitalize_choices(choices):
    return ((choice[0], choice[1].capitalize()) for choice in choices)


class PersonForm(ModelForm):

    first_name = forms.CharField(
        required=True,
        label=_("first_name")
    )

    last_name = forms.CharField(
        required=True,
        label=_("last_name")
    )

    gender = forms.ChoiceField(
        choices=_capitalize_choices(Person.GENDER_CHOICES),
        required=True,
        label=_("gender")
    )

    def __init__(self, *args, **kwargs):

        super(PersonForm, self).__init__(*args, **kwargs)

        if self.instance.pk:
            self._disable_existing_person_fields()

    def _disable_existing_person_fields(self):
        for field in self.fields.keys():
            self.fields[field].initial = getattr(self.instance, field)
            self.fields[field].widget.attrs['readonly'] = True
            if field is "gender":
                self.fields[field].widget.attrs['disabled'] = True

    class Meta:
        model = Person

        fields = [
            'first_name',
            'last_name',
            'email',
            'gender'
        ]

        # Automatic translation of field names
        labels = {field: _(field) for field in fields}
