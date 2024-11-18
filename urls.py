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
from django.urls import include, path, re_path

from continuing_education.forms.account import ContinuingEducationRegistrationForm
from continuing_education.views import account_activation, prospect
from continuing_education.views import (home, admission, registration, common, file)
from continuing_education.views.account_activation import (
    ContinuingEducationPasswordResetView,
    ContinuingEducationPasswordResetConfirmView,
)
from continuing_education.views.autocomplete.continuing_education_training import \
    ContinuingEducationTrainingAutocomplete

urlpatterns = [
    path('', home.formations_list, name='formations_list'),
    re_path(r'^set_lang/([A-Za-z-]+)/$', home.set_language, name='set_language'),
    path('home/', home.main_view, name='continuing_education_home'),
    re_path(r'^home/(?P<acronym>[\w]+)/$', home.main_view, name='continuing_education_home'),
    path('authentication/', include([
        path('login', common.login, name='continuing_education_login'),
        path('logout', common.log_out, name='continuing_education_logout'),
        path('logged_out', common.logged_out, name='continuing_education_logged_out')])),
    path('account/', include([
        path('register/',
            account_activation.ContinuingEducationRegistrationView.as_view(
                form_class=ContinuingEducationRegistrationForm
            ),
            name='django_registration_register'),
        path(
            'complete_account_registration/',
            account_activation.complete_account_registration,
            name='complete_account_registration'
        ),
        re_path(r'^activate/(?P<formation_id>[0-9a-f-]+)/(?P<activation_key>[-:\w]+)/$',
            account_activation.ContinuingEducationActivationView.as_view(),
            name='django_registration_activate'),
        re_path(r'^activate/(?P<activation_key>[-:\w]+)/$',
            account_activation.ContinuingEducationActivationView.as_view(),
            name='django_registration_activate'),
        path('password_reset/', ContinuingEducationPasswordResetView.as_view(), name='password_reset'),
        re_path(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/$',
            ContinuingEducationPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
        path('', include('django_registration.backends.activation.urls'))])),
    re_path(r'^admission_new/', admission.admission_form, name='admission_new'),
    re_path(r'^admission_edit/(?P<admission_uuid>[0-9a-f-]+)$', admission.admission_form, name='admission_edit'),
    re_path(r'^admission_detail/(?P<admission_uuid>[0-9a-f-]+)$', admission.admission_detail, name='admission_detail'),
    re_path(r'^admission_submit/', admission.admission_submit, name='admission_submit'),
    re_path(
        r'^registration_edit/(?P<admission_uuid>[0-9a-f-]+)$',
        registration.registration_edit,
        name='registration_edit'
    ),
    re_path(r'^registration_detail/(?P<admission_uuid>[0-9a-f-]+)$', registration.registration_detail,
        name='registration_detail'),
    re_path(r'^registration_pdf/(?P<admission_uuid>[0-9a-f-]+)$', registration.generate_pdf_registration,
        name='registration_pdf'),
    re_path(r'^registration_submit/', registration.registration_submit, name='registration_submit'),
    re_path(
        r'^download_file/(?P<file_uuid>[0-9a-f-]+)/(?P<admission_uuid>[0-9a-f-]+)',
        file.download_file,
        name="download_file"
    ),
    re_path(
        r'^remove_file/(?P<file_uuid>[0-9a-f-]+)/(?P<admission_uuid>[0-9a-f-]+)',
        file.remove_file,
        name="remove_file"
    ),
    re_path(
        r'^upload_file/(?P<admission_uuid>[0-9a-f-]+)',
        file.upload_file,
        name="upload_file"
    ),
    re_path(r'^prospect_form/(?P<acronym>[\w]+)/$', prospect.prospect_form, name='prospect_form'),
    path('prospect_form/', prospect.prospect_form, name='prospect_form'),
    path(
        'cetraining-autocomplete/',
        ContinuingEducationTrainingAutocomplete.as_view(),
        name='cetraining-autocomplete',
    ),
    re_path(r'^ajax/formation/', admission.get_formation_information, name='get_formation_information')
]
