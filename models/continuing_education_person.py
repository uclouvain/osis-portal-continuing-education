from django.db import models


class ContinuingEducationPerson(models.Model):

    person = models.OneToOneField('base.Person', on_delete=models.CASCADE)
    birth_location = models.CharField(max_length=255, blank=True)
    birth_country = models.ForeignKey('reference.Country', blank=True, null=True, related_name='birth_country')
    citizenship = models.ForeignKey('reference.Country', blank=True, null=True, related_name='citizenship')

    #Address
    location = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=255, blank=True)
    country = models.ForeignKey('reference.Country', blank=True, null=True, related_name='address_country')
