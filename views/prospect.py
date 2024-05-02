from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from continuing_education.forms.prospect import ProspectForm
from continuing_education.views import api
from continuing_education.views.api import post_prospect
from continuing_education.views.common import display_success_messages


def prospect_form(request, acronym=None):
    cet = None
    if acronym:
        cet = api.get_continuing_education_training(request, acronym)
    form = ProspectForm(request.POST or None, ce_training=cet)

    if form.is_valid():
        prospect = {
            'name': request.POST.get('name'),
            'first_name': request.POST.get('first_name'),
            'city': request.POST.get('city'),
            'postal_code': request.POST.get('postal_code'),
            'email': request.POST.get('email'),
            'formation': cet['uuid'],
            'phone_number': request.POST.get('phone_number')
        }
        data, response_status_code = post_prospect(request, prospect)
        if response_status_code == 201:
            display_success_messages(request, _("Your form has been correctly sent."))
    return render(request, 'prospect_form.html', locals())
