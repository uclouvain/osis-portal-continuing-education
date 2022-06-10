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
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.backends import UserModel
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordContextMixin, INTERNAL_RESET_SESSION_TOKEN
from django.contrib.sites.shortcuts import get_current_site
from django.core import signing
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import FormView
from django_registration import signals
from django_registration.exceptions import ActivationError
from django_registration.views import RegistrationView, ActivationView

from base.models.person import Person
from base.views.layout import render
from continuing_education.forms.account import ContinuingEducationPersonForm, ContinuingEducationPasswordResetForm
from continuing_education.forms.address import AddressForm
from continuing_education.forms.admission import AdmissionForm
from continuing_education.forms.person import PersonForm
from continuing_education.views.common import display_errors
from osis_common.messaging import message_config, send_message as message_service

REGISTRATION_SALT = getattr(settings, 'REGISTRATION_SALT', 'registration')


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
        if self.request.session.get('formation_id'):
            del self.request.session['formation_id']
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
        params = {'activation_key': activation_key}
        if self.request.session.get('formation_id'):
            params.update({'formation_id': self.request.session.get('formation_id')})
        url = reverse('django_registration_activate', kwargs=params)
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
        error_message = message_service.send_messages(
            message_content,
            settings.IUFC_CONFIG.get('ACTIVATION_MESSAGES_OUTSIDE_PRODUCTION')
        )


@login_required
def complete_account_registration(request):
    if request.POST:
        return __post_complete_account_registration(request)
    else:
        return redirect(reverse('admission_new'))


def __post_complete_account_registration(request):
    root_person_form = PersonForm(request.POST)
    ce_person_form = ContinuingEducationPersonForm(request.POST)
    address_form = AddressForm(request.POST)
    admission_form = AdmissionForm(request.POST)
    forms = [root_person_form, ce_person_form, address_form, admission_form]
    errors = []
    if all([f.is_valid() for f in forms]):
        address = address_form.save()
        person = root_person_form.save(commit=False)
        person.user = request.user
        person.email = request.user.username
        person.save()
        continuing_education_person = ce_person_form.save(commit=False)
        continuing_education_person.person = person
        continuing_education_person.save()
        admission = admission_form.save(commit=False)
        admission.person_information = continuing_education_person
        admission.address = address
        admission.save()
        if request.session.get('formation_id'):
            del request.session['formation_id']
        return redirect(reverse('continuing_education_home'))
    else:
        for f in forms:
            errors.append(f.errors)
        display_errors(request, errors)

    return render(request, 'django_registration/complete_account_registration.html', locals())


class ContinuingEducationActivationView(ActivationView):
    """
    Given a valid activation key, activate the user's
    account. Otherwise, show an error message stating the account
    couldn't be activated.

    """
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
    success_url = None

    def activate(self, *args, **kwargs):
        username = self.validate_key(kwargs.get('activation_key'))
        formation_id = kwargs.get('formation_id')
        user = self.get_user(username)
        user.is_active = True
        user.save()
        Person.objects.get_or_create(user=user, email=user.username, defaults={'language': 'fr-be'})
        self.request.session['formation_id'] = formation_id
        return user

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

    def get(self, *args, **kwargs):
        """
        The base activation logic; subclasses should leave this method
        alone and implement activate(), which is called from this
        method.

        """
        extra_context = {}
        try:
            activated_user = self.activate(*args, **kwargs)
        except ActivationError as e:
            extra_context['activation_error'] = {
                'message': e.message,
                'code': e.code,
                'params': e.params
            }
        else:
            signals.user_activated.send(
                sender=self.__class__,
                user=activated_user,
                request=self.request
            )
            login(self.request, activated_user, backend='django.contrib.auth.backends.ModelBackend')
            return HttpResponseRedirect(
                force_text(
                    self.get_success_url(activated_user)
                )
            )
        context_data = self.get_context_data()
        context_data.update(extra_context)
        return self.render_to_response(context_data)

    def get_success_url(self, user=None):
        if not user:
            raise ActivationError(
                self.BAD_USERNAME_MESSAGE,
                code='bad_username'
            )
        return force_text(reverse("complete_account_registration"))


class ContinuingEducationPasswordResetView(PasswordContextMixin, FormView):
    form_class = ContinuingEducationPasswordResetForm
    from_email = None
    success_url = reverse_lazy('continuing_education_login')
    template_name = 'registration/continuing_education_password_reset_form.html'
    token_generator = default_token_generator
    title = _('Password reset')
    reset_url_token = "set-password"

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super(ContinuingEducationPasswordResetView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        opts = {
            'token_generator': self.token_generator,
            'request': self.request
        }
        error_message = form.save(**opts)
        if error_message:
            messages.add_message(self.request, messages.ERROR, error_message, "alert-danger")
            return redirect(reverse('password_reset'))
        success_message = _('An email was sent to you with the instructions to change your password. '
                            'You should receive this email shortly.')
        messages.add_message(self.request, messages.INFO, success_message, "alert-info")
        return super(ContinuingEducationPasswordResetView, self).form_valid(form)


class ContinuingEducationPasswordResetConfirmView(PasswordContextMixin, FormView):
    form_class = SetPasswordForm
    post_reset_login = True
    post_reset_login_backend = 'django.contrib.auth.backends.ModelBackend'
    success_url = reverse_lazy('continuing_education_home')
    template_name = 'registration/continuing_education_password_reset_confirm.html'
    title = _('Enter a new password')
    token_generator = default_token_generator
    reset_url_token = "set-password"

    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        assert 'uidb64' in kwargs and 'token' in kwargs

        self.validlink = False
        self.user = self.get_user(kwargs['uidb64'])

        if self.user is not None:
            token = kwargs['token']
            if token == self.reset_url_token:
                session_token = self.request.session.get(INTERNAL_RESET_SESSION_TOKEN)
                if self.token_generator.check_token(self.user, session_token):
                    # If the token is valid, display the password reset form.
                    self.validlink = True
                    return super(ContinuingEducationPasswordResetConfirmView, self).dispatch(*args, **kwargs)
            else:
                if self.token_generator.check_token(self.user, token):
                    # Store the token in the session and redirect to the
                    # password reset form at a URL without the token. That
                    # avoids the possibility of leaking the token in the
                    # HTTP Referer header.
                    self.request.session[INTERNAL_RESET_SESSION_TOKEN] = token
                    redirect_url = self.request.path.replace(token, self.reset_url_token)
                    return HttpResponseRedirect(redirect_url)

        # Display the "Password reset unsuccessful" page.
        return self.render_to_response(self.get_context_data())

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring on Python 3
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = UserModel._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
            user = None
        return user

    def get_form_kwargs(self):
        kwargs = super(ContinuingEducationPasswordResetConfirmView, self).get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs

    def form_valid(self, form):
        user = form.save()
        del self.request.session[INTERNAL_RESET_SESSION_TOKEN]
        success_message = _('Your password was successfully changed.')
        messages.add_message(self.request, messages.INFO, success_message, "alert-info")
        if self.post_reset_login:
            login(self.request, user, self.post_reset_login_backend)
        return super(ContinuingEducationPasswordResetConfirmView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(ContinuingEducationPasswordResetConfirmView, self).get_context_data(**kwargs)
        if self.validlink:
            context['validlink'] = True
        else:
            context.update({
                'form': None,
                'title': _('Password reset unsuccessful'),
                'validlink': False,
            })
        return context
