from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from base.models.person import Person


class PersonForm(ModelForm):

    def __init__(self, *args, **kwargs):

        super(PersonForm, self).__init__(*args, **kwargs)

        for field in self.fields.keys():
            self.fields[field].initial = getattr(self.instance, field)
            self.fields[field].widget.attrs['readonly'] = True
            if field is "gender":
                self.fields[field].widget.attrs['disabled'] = True

    def clean_gender(self):
        if self.instance.gender:
            return self.instance.gender
        else:
            gender = self.cleaned_data['gender']
            return gender

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
