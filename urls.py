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
from django.conf.urls import url, include

from continuing_education.views import (home, admission, registration, common)
from continuing_education.views import account_activation

urlpatterns = [
    url(r'^$', home.formations_list, name='formations_list'),
    url(r'^home/$', home.main_view, name='continuing_education_home'),
    url(r'^home/(?P<formation_id>[0-9]+)$', home.main_view, name='continuing_education_home'),
    url(r'^authentication/', include([
        url(r'^login$', common.login, name='continuing_education_login'),
        url(r'^logout$', common.log_out, name='continuing_education_logout'),
        url(r'^logged_out$', common.logged_out, name='continuing_education_logged_out')])),
    url(r'^account/', include([
        url(r'^register/$',
            account_activation.ContinuingEducationRegistrationView.as_view(),
            name='django_registration_register'),
        url(r'^complete_account_registration/$', account_activation.complete_account_registration, name='complete_account_registration'),
        url(r'^', include('django_registration.backends.activation.urls'))])),
    url(r'^admission_new/', admission.admission_new, name='admission_new'),
    url(r'^admission_edit/(?P<admission_id>[0-9]+)$', admission.admission_edit, name='admission_edit'),
    url(r'^admission_detail/(?P<admission_id>[0-9]+)$', admission.admission_detail, name='admission_detail'),
    url(r'^registration_edit/(?P<admission_id>[0-9]+)$', registration.registration_edit, name='registration_edit'),
    url(r'^registration_detail/(?P<admission_id>[0-9]+)$', registration.registration_detail,
        name='registration_detail')
]
