from django.contrib import admin

from continuing_education.models import admission, continuing_education_training, person_training, \
    continuing_education_person, address

admin.site.register(
    admission.Admission,
    admission.AdmissionAdmin
)
admin.site.register(
    continuing_education_person.ContinuingEducationPerson,
    continuing_education_person.ContinuingEducationPersonAdmin
)
admin.site.register(
    address.Address,
    address.AddressAdmin
)
admin.site.register(
    continuing_education_training.ContinuingEducationTraining,
    continuing_education_training.ContinuingEducationTrainingAdmin,
)
admin.site.register(
    person_training.PersonTraining,
    person_training.PersonTrainingAdmin,
)
