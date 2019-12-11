import json

from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from openapi_client.rest import ApiException
from rest_framework import status

from continuing_education.forms.prospect import ProspectForm
from continuing_education.views.common import display_success_messages, display_error_messages
from continuing_education.views.utils import sdk


def prospect_form(request, formation_uuid=None):
    cet = None
    if formation_uuid:
        cet = sdk.get_continuing_education_training(formation_uuid)
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
        try:
            data = sdk.post_prospect(prospect)
            display_success_messages(request, _("Your form was correctly send."))
            return redirect(reverse('continuing_education_home'))
        except ApiException as e:
            display_error_messages(request, json.loads(e.body))
    return render(request, 'prospect_form.html', locals())
