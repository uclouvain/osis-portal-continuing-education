from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from base.models.person import Person


class PersonForm(ModelForm):

    def __init__(self, *args, **kwargs):
        user_email = kwargs.pop('user_email', None)
        first_name = kwargs.pop('first_name', None)
        last_name = kwargs.pop('last_name', None)
        gender = kwargs.pop('gender', None)

        super(PersonForm, self).__init__(*args, **kwargs)
        if user_email:
            self.fields['email'].initial = user_email
            self.fields['email'].widget.attrs['readonly'] = True
        if first_name:
            self.fields['first_name'].initial = first_name
            self.fields['first_name'].widget.attrs['readonly'] = True
        if last_name:
            self.fields['last_name'].initial = last_name
            self.fields['last_name'].widget.attrs['readonly'] = True
        if gender:
            self.fields['gender'].initial = gender
            self.fields['gender'].widget.attrs['disabled'] = True

    class Meta:
        model = Person
        # automatic translation of field names
        fields = [
            'first_name',
            'last_name',
            'email',
            'gender'
        ]
        labels = {field: _(field) for field in fields}
