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
import io
from mimetypes import MimeTypes

import requests
from dateutil import parser
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.text import get_valid_filename
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.parsers import JSONParser

from continuing_education.models.admission import Admission
from continuing_education.views.api import _prepare_headers_for_files
from continuing_education.views.common import display_error_messages, display_success_messages

MAX_ADMISSION_FILE_NAME_LENGTH = 100


@login_required
def upload_file(request, admission_uuid):
    admission_file = request.FILES['myfile'] if 'myfile' in request.FILES else None
    admission = Admission.objects.get(uuid=admission_uuid)
    person = admission.person_information.person
    data = {
        'uploaded_by': person.uuid,
    }
    url = settings.URL_CONTINUING_EDUCATION_FILE_API + "admissions/" + str(admission.uuid) + "/files/"
    headers_to_upload = {
        'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN,
    }

    request_to_upload = requests.post(
        url,
        headers=headers_to_upload,
        files={'path': admission_file},
        data=data
    )

    if request_to_upload.status_code == status.HTTP_201_CREATED:
        display_success_messages(request, _("The document is uploaded correctly"))
    else:
        display_error_messages(request, request_to_upload.json())

    return redirect(request.META.get('HTTP_REFERER')+'#documents')


@login_required
def download_file(request, file_uuid, admission_uuid):
    url = settings.URL_CONTINUING_EDUCATION_FILE_API + \
          "admissions/" + str(admission_uuid) + "/files/" + str(file_uuid)
    headers_to_get = {
        'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN
    }
    request_to_get = requests.get(
        url,
        headers=headers_to_get
    )
    if request_to_get.status_code == status.HTTP_200_OK:
        stream = io.BytesIO(request_to_get.content)
        admission_file = JSONParser().parse(stream)
        name = get_valid_filename(admission_file['name'])
        mime_type = MimeTypes().guess_type(admission_file['name'])
        response_file = base64.b64decode(admission_file['content'])
        response = HttpResponse(response_file, mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % name
        return response
    else:
        return HttpResponse(status=404)


@login_required
def remove_file(request, file_uuid, admission_uuid):
    url = settings.URL_CONTINUING_EDUCATION_FILE_API + \
          "admissions/" + str(admission_uuid) + "/files/" + str(file_uuid)
    headers_to_delete = {
        'Authorization': 'Token ' + settings.OSIS_PORTAL_TOKEN
    }
    request_to_delete = requests.delete(
        url,
        headers=headers_to_delete
    )

    if request_to_delete.status_code == status.HTTP_204_NO_CONTENT:
        display_success_messages(request, _("File correctly deleted"))
    else:
        display_error_messages(request, _("A problem occured during delete"))
    return redirect(request.META.get('HTTP_REFERER')+'#documents')


def _get_files_list(admission, url_continuing_education_file_api):
    """
    Get files list of an admission with OSIS IUFC API
    """
    files_list = []
    response = requests.get(
        url=url_continuing_education_file_api,
        headers=_prepare_headers_for_files('GET'),
    )
    if response.status_code == status.HTTP_200_OK:
        stream = io.BytesIO(response.content)
        files_list = JSONParser().parse(stream)['results']
        for file in files_list:
            file['created_date'] = parser.parse(
                file['created_date']
            )
            file['is_deletable'] = _is_file_uploaded_by_admission_person(admission, file)
    return files_list


def _is_file_uploaded_by_admission_person(admission, file):
    uploaded_by = file.get('uploaded_by', None)
    uploader_uuid = uploaded_by.get('uuid', None) if uploaded_by else None
    return uploader_uuid == str(admission.person_information.person.uuid)
