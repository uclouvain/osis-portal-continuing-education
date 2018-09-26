from django.forms import ModelForm

from base.models.person import Person


class PersonForm(ModelForm):

    def __init__(self, *args, **kwargs):
        user_email = kwargs.pop('user_email', None)
        super(PersonForm, self).__init__(*args, **kwargs)
        if user_email:
            self.fields['email'].initial = user_email
            self.fields['email'].widget.attrs['readonly'] = True

    class Meta:
        model = Person
        # automatic translation of field names
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone_mobile',
            'gender'
        ]
