##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################

from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import translation

from base.models import person as mdl_person
from continuing_education.views import api


def formations_list(request):
    limit = 10
    if request.user.is_authenticated:
        return redirect(main_view)
    try:
        active_page = int(request.GET.get('page'))
    except TypeError:
        active_page = 1
    paginator = api.get_continuing_education_training_list(
        limit=limit,
        offset=(active_page - 1) * limit,
    )
    formations = paginator['results']
    pages_count = round(paginator['count'] / limit)
    return render(request, "continuing_education/formations.html", {
        'formations': formations,
        'pages_count': range(1, pages_count + 1),
        'active_page': active_page
    })


def main_view(request, formation_id=None):
    if formation_id:
        request.session['formation_id'] = formation_id
    if request.user.is_authenticated:
        api.get_personal_token(request)
        person = mdl_person.find_by_user(request.user)

        person_information = api.get_continuing_education_person(request)
        admissions = api.get_admission_list(request, person_information['uuid'])['results']
        registrations = api.get_registration_list(request, person_information['uuid'])['results']

        return render(request, "continuing_education/home.html", locals())
    else:
        if formation_id:
            is_active = api.get_continuing_education_training(request, formation_id)['active']
            if not is_active:
                return redirect(reverse('prospect_form', kwargs={'formation_uuid': formation_id}))
        return render(request, "authentication/login.html")


def set_language(request, ui_language):
    translation.activate(ui_language)
    request.session[translation.LANGUAGE_SESSION_KEY] = ui_language
    return redirect(request.META['HTTP_REFERER'])
