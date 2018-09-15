from django.contrib.auth.models import User
from django.forms import ModelForm, IntegerField, HiddenInput

from base.models.person import Person
from django.utils.translation import ugettext_lazy as _


class PersonForm(ModelForm):

    user_id = IntegerField(widget=HiddenInput, required=True)

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id', None)
        super(PersonForm, self).__init__(*args, **kwargs)
        if user_id:
            user = User.objects.get(id=user_id)
            self.fields['user_id'].initial = int(user_id)
            self.fields['email'].initial = user.email
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
        labels = {field: _(field) for field in fields}
