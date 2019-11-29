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
import base64
import json
import os
from mimetypes import MimeTypes

import requests
from dateutil import parser
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import model_to_dict
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.text import get_valid_filename
from django.utils.translation import gettext_lazy as _
from openapi_client.rest import ApiException

from continuing_education.views.api import get_admission, get_registration, get_files_list, get_file, \
    delete_file, upload_file as api_upload_file
from continuing_education.views.common import display_error_messages, display_success_messages

MAX_ADMISSION_FILE_NAME_LENGTH = 100
FILES_URL = settings.URL_CONTINUING_EDUCATION_FILE_API + "/admissions/%(admission_uuid)s/files/"


@login_required
def upload_file(request, admission_uuid):
    admission_file = request.FILES['myfile']

    try:
        admission = get_admission(request, admission_uuid)
    except Http404:
        admission = get_registration(request, admission_uuid)

    try:
        api_upload_file(
            request,
            admission_uuid,
            path=admission_file,
            uploaded_by=admission['person_uuid']
        )
        display_success_messages(request, _("The document is uploaded correctly"))
    except ApiException as e:
        display_error_messages(request, json.loads(e.body))

    return redirect(request.META.get('HTTP_REFERER') + '#documents')


@login_required
def download_file(request, file_uuid, admission_uuid):
    try:
        admission_file = get_file(request, admission_uuid, file_uuid)
        name = get_valid_filename(admission_file['name'])
        mime_type = MimeTypes().guess_type(admission_file['name'])
        response_file = base64.b64decode(admission_file['content'])
        response = HttpResponse(response_file, mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % name
        return response
    except Exception:
        display_error_messages(request, _('An unexpected error occurred during download'))
    return redirect(request.META.get('HTTP_REFERER') + '#documents')


@login_required
def remove_file(request, file_uuid, admission_uuid):
    try:
        delete_file(request, admission_uuid, file_uuid)
        display_success_messages(request, _("File correctly deleted"))
    except Exception:
        display_error_messages(request, _("A problem occured during delete"))
    return redirect(request.META.get('HTTP_REFERER') + '#documents')


def _get_files_list(request, admission):
    """
    Get files list of an admission with OSIS IUFC API
    """
    files_list = []
    try:
        files_list = get_files_list(request, admission['uuid'])['results']
        for file in files_list:
            file['created_date'] = parser.parse(
                file['created_date']
            )
            file['is_deletable'] = _is_file_uploaded_by_admission_person(admission, file)
    except requests.exceptions.ConnectionError:
        display_error_messages(request, _('An unexpected error occurred'))
    return files_list


def _is_file_uploaded_by_admission_person(admission, file):
    uploaded_by = file.get('uploaded_by', None)
    uploader_uuid = uploaded_by.get('uuid', None) if uploaded_by else None
    return uploader_uuid == str(admission['person_uuid'])
