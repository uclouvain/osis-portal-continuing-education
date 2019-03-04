from django.shortcuts import redirect, render
from django.urls import reverse

from continuing_education.forms.prospect import ProspectForm


def prospect_form(request):
    form = ProspectForm(request.POST or None)
    if form.is_valid():
        prospect = form.save()
        return redirect(reverse('continuing_education_home'))
    return render(request, 'prospect_form.html', locals())
