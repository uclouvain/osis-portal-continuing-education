from datetime import datetime

from django.contrib.admin import ModelAdmin
from django.db import models
from django.utils.translation import ugettext_lazy as _


class ContinuingEducationPersonAdmin(ModelAdmin):
    list_display = ('person', 'citizenship', 'email',)
    search_fields = ['first_name', 'last_name', 'email']
    list_filter = ('activity_sector', 'citizenship')

class ContinuingEducationPerson(models.Model):

    GENDER_CHOICES = (
        ('F', _('female')),
        ('M', _('male')),
    )

    STATUS_CHOICES = (
        ('EMPLOYEE', _('employee')),
        ('SELF_EMPLOYED', _('self_employed')),
        ('JOB_SEEKER', _('job_seeker')),
        ('PUBLIC_SERVANT', _('public_servant')),
        ('OTHER', _('other')),
    )

    SECTOR_CHOICES = (
        ('PRIVATE', _('private')),
        ('PUBLIC', _('public')),
        ('ASSOCIATIVE', _('associative')),
        ('HEALTH', _('health')),
        ('OTHER', _('other')),
    )

    person = models.OneToOneField('base.Person', on_delete=models.CASCADE)

    birth_location = models.CharField(max_length=255, blank=True)
    birth_country = models.ForeignKey('reference.Country', blank=True, null=True, related_name='birth_country')
    citizenship = models.ForeignKey('reference.Country', blank=True, null=True, related_name='citizenship')

    # Contact
    address = models.ForeignKey('continuing_education.Address', blank=True, null=True)
    phone_mobile = models.CharField(max_length=30, blank=True)
    email = models.EmailField(max_length=255, blank=True)

    # Education
    high_school_diploma = models.BooleanField(default=False)
    high_school_graduation_year = models.DateField(blank=True, default=datetime.now)
    last_degree_level = models.CharField(max_length=50, blank=True)
    last_degree_field = models.CharField(max_length=50, blank=True)
    last_degree_institution = models.CharField(max_length=50, blank=True)
    last_degree_graduation_year = models.DateField(blank=True, default=datetime.now)
    other_educational_background = models.TextField(blank=True)

    # Professional Background
    professional_status = models.CharField(max_length=50, blank=True, choices=STATUS_CHOICES)
    current_occupation = models.CharField(max_length=50, blank=True)
    current_employer = models.CharField(max_length=50, blank=True)
    activity_sector = models.CharField(max_length=50, blank=True, choices=SECTOR_CHOICES)
    past_professional_activities = models.TextField(blank=True)

    def __str__(self):
        return "{} - {} {} - {}".format(self.id, self.person.first_name, self.person.last_name, self.person.email)


def find_by_person(person):
    return ContinuingEducationPerson.objects.filter(person=person).first()
