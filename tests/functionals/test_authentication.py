from django.conf import settings
from django.core import mail
from django.core import signing
from django.test import override_settings

from base.tests.factories.user import UserFactory
from base.tests.functional.models.user_type import UserMixin
from osis_common.tests.functional.models.model import FunctionalTestCase
from osis_common.tests.functional.models.report import can_be_reported


class TestAuthentication(FunctionalTestCase, UserMixin):
    """
    User authentication process testing
    """

    @classmethod
    def setUpClass(cls):
        super(TestAuthentication, cls).setUpClass()
        cls.continuing_education_config = cls.config.get('CONTINUING_EDUCATION')

    def setUp(self):
        super(TestAuthentication, self).setUp()
        self.valid_user = UserFactory()

    @can_be_reported
    def test_valid_user(self):
        """
        As a valid user
         I should be able to login into the Continuing Education application
        """
        self.login(username=self.valid_user.username, login_page_name='continuing_education_login')
        self.wait_until_title_is(self.continuing_education_config.get('PAGE_TITLE'))

    @can_be_reported
    def test_non_valid_user(self):
        """
        As a non valid user
         I should not be able to login into the Continuing Education application
        """
        self.login(username='non_valid_user', login_page_name='continuing_education_login')
        self.wait_until_title_is('Login')


class TestRegistration(FunctionalTestCase, UserMixin):
    """
    User registration process testing
    """

    @classmethod
    def setUpClass(cls):
        super(TestRegistration, cls).setUpClass()
        cls.continuing_education_config = cls.config.get('CONTINUING_EDUCATION')

    def setUp(self):
        super(TestRegistration, self).setUp()
        self.valid_user = UserFactory()

    @can_be_reported
    def test_access_registration_page(self):
        """
        As a non registered user
         I should be able to Access the new user registration page
        """
        self.__go_to_registration_page()
        self.wait_until_title_is('User Registration')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @can_be_reported
    def test_first_step_registration_success(self):
        """
        As a non registered user
         If i go to the registration page and enter valid information in the register form
         - I should be able to register
         - I should receive an email with an activation link.
        """
        username, password = self.__register_user()
        self.wait_until_title_is('Registration Complete')
        self.assertTrue(len(mail.outbox) == 1)
        self.assertEqual(mail.outbox[0].subject,
                         self.get_localized_message('continuing_education_activation_email_subject', 'en'))
        activation_url = self.get_link_href_by_url_name('django_registration_activate',
                                                        {'activation_key': self.__get_activation_key(username)})
        mail_body = mail.outbox[0].body
        self.assertTrue(activation_url in mail_body)

    @can_be_reported
    def test_registered_user_not_activated_account(self):
        """
        As a registered user
        If i have not activated my account yet
        - I should not be able to log into the application
        """
        username, password = self.__register_user()
        self.login(username=username, password=password, login_page_name='continuing_education_login')
        self.wait_until_title_is('Login')

    @can_be_reported
    def test_activate_account(self):
        """
        As a registered user
        If i have not activated my account yet
        If i go to the activation link i've received by email
        - I should see an activation message
        - I should be able to login with my account
        """
        from base.models.person import Person
        username, password = self.__register_user()
        self.open_url_by_name('django_registration_activate', {'activation_key': self.__get_activation_key(username)})
        self.wait_until_title_is('Activation Complete')
        self.login(username=username, password=password, login_page_name='continuing_education_login')
        self.assertIsNotNone(Person.objects.get(user__username=username))
        self.wait_until_title_is(self.continuing_education_config.get('PAGE_TITLE'))

    def __go_to_registration_page(self):
        self.open_url_by_name('continuing_education_home')
        self.click_element_by_id('signup_btn')

    def __register_user(self):
        username = 'tes_user'
        email = 'test_user@test.org'
        password = 'password'
        self.__go_to_registration_page()
        self.fill_element_by_id('id_username', username)
        self.fill_element_by_id('id_email', email)
        self.fill_element_by_id('id_password1', password)
        self.fill_element_by_id('id_password2', password)
        self.click_element_by_id('bt_submit_registration')
        return username, password

    @staticmethod
    def __get_activation_key(username):
        registration_salt = getattr(settings, 'REGISTRATION_SALT', 'registration')
        return signing.dumps(obj=username, salt=registration_salt)
