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
import json
import os

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, redirect

from base.models import person as mdl_person
from continuing_education.models import admission
from continuing_education.models.enums import admission_state_choices
from continuing_education.views.common import get_data_list_from_osis


def formations_list(request):
    if request.user.is_authenticated():
        return redirect(main_view)
    formations = fetch_example_data()
    paginator = Paginator(formations, 10)
    page = request.GET.get('page')
    try:
        formations = paginator.page(page)
    except PageNotAnInteger:
        formations = paginator.page(1)
    except EmptyPage:
        formations = paginator.page(paginator.num_pages)
    return render(request, "continuing_education/formations.html", {
        'formations': formations
    })


def main_view(request, formation_id=None):
    if formation_id:
        request.session['formation_id'] = formation_id
    if request.user.is_authenticated:
        person = mdl_person.find_by_user(request.user)
        continuing_education_person = get_data_list_from_osis("persons", "person", str(person))[0]
        admissions = get_data_list_from_osis("admissions", "person", str(person))
        registrations = admission.search(
            person__uuid=continuing_education_person['person']['uuid'],
            state__in=[admission_state_choices.ACCEPTED, admission_state_choices.REGISTRATION_SUBMITTED],
        )
        return render(request, "continuing_education/home.html", locals())
    else:
        return render(request, "authentication/login.html")


def fetch_example_data():
    # get formations from temporary file
    module_dir = os.path.dirname(__file__)
    file_path = os.path.join(module_dir, 'example_data.json')
    with open(file_path) as f:
        data = json.load(f)
    return sorted(data, key=lambda k: k['acronym'])
