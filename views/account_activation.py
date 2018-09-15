##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core import signing
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django_registration import signals
from django_registration.exceptions import ActivationError
from django_registration.views import ActivationView, RegistrationView

import base.models.person as mdl_person
from base.views.layout import render
from continuing_education.forms.account import ContinuingEducationPersonForm
from continuing_education.forms.person import PersonForm
from continuing_education.views.common import display_errors
from osis_common.messaging import message_config, send_message as message_service

REGISTRATION_SALT = getattr(settings, 'REGISTRATION_SALT', 'registration')


class ContinuingEducationActivationView(ActivationView):
    user = None

    ALREADY_ACTIVATED_MESSAGE = _(
        u'The account you tried to activate has already been activated.'
    )
    BAD_USERNAME_MESSAGE = _(
        u'The account you attempted to activate is invalid.'
    )
    EXPIRED_MESSAGE = _(u'This account has expired.')
    INVALID_KEY_MESSAGE = _(
        u'The activation key you provided is invalid.'
    )

    def get_success_url(self, user=None):
        user_id = self.user.id
        return reverse('complete_activation_get', kwargs={'user_id': user_id})

    def activate(self, *args, **kwargs):
        username = self.validate_key(kwargs.get('activation_key'))
        self.user = self.get_user(username)
        self.user.is_active = True
        self.user.save()
        return self.user

    def validate_key(self, activation_key):
        """
        Verify that the activation key is valid and within the
        permitted activation time window, returning the username if
        valid or raising ``ActivationError`` if not.

        """
        try:
            username = signing.loads(
                activation_key,
                salt=REGISTRATION_SALT,
                max_age=settings.ACCOUNT_ACTIVATION_DAYS * 86400
            )
            return username
        except signing.SignatureExpired:
            raise ActivationError(
                self.EXPIRED_MESSAGE,
                code='expired'
            )
        except signing.BadSignature:
            raise ActivationError(
                self.INVALID_KEY_MESSAGE,
                code='invalid_key',
                params={'activation_key': activation_key}
            )

    def get_user(self, username):
        """
        Given the verified username, look up and return the
        corresponding user account if it exists, or raising
        ``ActivationError`` if it doesn't.

        """
        User = get_user_model()
        try:
            user = User.objects.get(**{
                User.USERNAME_FIELD: username,
            })
            if user.is_active:
                raise ActivationError(
                    self.ALREADY_ACTIVATED_MESSAGE,
                    code='already_activated'
                )
            return user
        except User.DoesNotExist:
            raise ActivationError(
                self.BAD_USERNAME_MESSAGE,
                code='bad_username'
            )


class ContinuingEducationRegistrationView(RegistrationView):
    success_url = reverse_lazy('django_registration_complete')
    html_template_ref = 'continuing_education_account_ativation_html'
    txt_template_ref = 'continuing_education_account_ativation_txt'

    def register(self, form):
        new_user = self.create_inactive_user(form)
        signals.user_registered.send(
            sender=self.__class__,
            user=new_user,
            request=self.request
        )
        return new_user

    def create_inactive_user(self, form):
        """
        Create the inactive user account and send an email containing
        activation instructions.

        """
        new_user = form.save(commit=False)
        new_user.is_active = False
        new_user.save()
        self.send_activation_email(new_user)
        return new_user

    @staticmethod
    def get_activation_key(user):
        """
        Generate the activation key which will be emailed to the user.

        """
        return signing.dumps(
            obj=user.get_username(),
            salt=REGISTRATION_SALT
        )

    def __get_activation_link(self, activation_key):
        scheme = 'https' if self.request.is_secure() else 'http'
        site = get_current_site(self.request)
        url = reverse('django_registration_activate', kwargs={'activation_key': activation_key})
        return '{scheme}://{site}{url}'.format(scheme=scheme,
                                               site=site,
                                               url=url)

    def send_activation_email(self, user):
        """
        Send the activation email. The activation key is the username,
        signed using TimestampSigner.

        """
        activation_key = self.get_activation_key(user)
        receivers = [message_config.create_receiver(user.id, user.email, None)]

        template_base_data = {
            'activation_link': self.__get_activation_link(activation_key),

        }
        message_content = message_config.create_message_content(self.html_template_ref, self.txt_template_ref,
                                                                [], receivers, template_base_data, None)
        message_service.send_messages(message_content)


def complete_activation(request, user_id=None):
    if request.POST:
        return __post_complete_activation(request)
    else:
        return __get_complete_activation(request, user_id)


def __get_complete_activation(request, user_id):
    user = User.objects.get(id=user_id)
    person = mdl_person.find_by_user(user=user)
    if person:
        return redirect('django_registration/informations_already_completed.html')
    root_person_form = PersonForm(user_id=user_id)
    ce_person_form = ContinuingEducationPersonForm()
    return render(request, 'django_registration/activation_complete.html', locals())


def __post_complete_activation(request):
    root_person_form = PersonForm(request.POST)
    ce_person_form = ContinuingEducationPersonForm(request.POST)
    errors = []
    if root_person_form.is_valid() and ce_person_form.is_valid():
        user = User.objects.get(id=root_person_form.cleaned_data['user_id'])
        person = root_person_form.save(commit=False)
        person.user = user
        person.save()
        continuing_education_person = ce_person_form.save(commit=False)
        continuing_education_person.person = person
        continuing_education_person.save()
        return redirect(reverse('continuing_education_login'))
    else:
        errors.append(root_person_form.errors)
        errors.append(ce_person_form.errors)
        display_errors(request, errors)
    return render(request, 'django_registration/activation_complete.html', locals())
