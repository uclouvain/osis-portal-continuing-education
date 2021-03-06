from django.utils.translation import gettext_lazy as _

ACCEPTED = 'Accepted'
ACCEPTED_NO_REGISTRATION_REQUIRED = 'Accepted (no registration required)'
REJECTED = 'Rejected'
WAITING = 'Waiting'

DRAFT = 'Draft'
SUBMITTED = 'Submitted'
REGISTRATION_SUBMITTED = 'Registration submitted'
VALIDATED = 'Validated'

ADMIN_STATE_CHOICES = (
    (ACCEPTED, _('Accepted')),
    (REJECTED, _('Rejected')),
    (WAITING, _('Waiting')),
    (VALIDATED, _('Validated')),
)

STUDENT_STATE_CHOICES = (
    (DRAFT, _('Draft')),
    (SUBMITTED, _('Submitted')),
    (REGISTRATION_SUBMITTED, _('Registration submitted'))
)

STATE_CHOICES = ADMIN_STATE_CHOICES + STUDENT_STATE_CHOICES
