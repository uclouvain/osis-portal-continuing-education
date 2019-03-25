from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import status

from continuing_education.forms.prospect import ProspectForm
from continuing_education.views.api import post_prospect, get_continuing_education_training
from continuing_education.views.common import display_success_messages


def prospect_form(request, formation_uuid=None):
    cet = None
    if formation_uuid:
        cet = get_continuing_education_training(formation_uuid)
    form = ProspectForm(request.POST or None, ce_training=cet)

    if form.is_valid():
        prospect = {
            'name': request.POST.get('name'),
            'first_name': request.POST.get('first_name'),
            'city': request.POST.get('city'),
            'postal_code': request.POST.get('postal_code'),
            'email': request.POST.get('email'),
            'formation': formation_uuid,
            'phone_number': request.POST.get('phone_number')
        }
        data, response_status_code = post_prospect(request, prospect)
        if response_status_code == status.HTTP_201_CREATED:
            display_success_messages(request, _("Your form was correctly send."))
            return redirect(reverse('continuing_education_home'))
    return render(request, 'prospect_form.html', locals())
