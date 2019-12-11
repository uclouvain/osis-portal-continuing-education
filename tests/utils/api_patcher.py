from unittest.mock import patch

from base.tests.factories.person import PersonFactory
from continuing_education.models.enums.admission_state_choices import ACCEPTED, SUBMITTED
from continuing_education.tests.factories.admission import AdmissionDictFactory, RegistrationDictFactory
from continuing_education.tests.factories.continuing_education_training import ContinuingEducationTrainingDictFactory
from continuing_education.tests.factories.person import ContinuingEducationPersonDictFactory


def api_create_patcher(test_case_instance):
    test_case_instance.get_admission_list_patcher = patch(
        "continuing_education.views.utils.sdk.get_admission_list",
        return_value={'results': [
            AdmissionDictFactory(
                person_information=ContinuingEducationPersonDictFactory(PersonFactory().uuid),
                state=SUBMITTED,
                formation=ContinuingEducationTrainingDictFactory()
            )
        ]}
    )
    test_case_instance.get_registration_list_patcher = patch(
        "continuing_education.views.utils.sdk.get_registration_list",
        return_value={'results': [
            AdmissionDictFactory(
                person_information=ContinuingEducationPersonDictFactory(PersonFactory().uuid),
                state=ACCEPTED,
                formation=ContinuingEducationTrainingDictFactory()
            )
        ]}
    )
    test_case_instance.get_continuing_education_training_list_patcher = patch(
        "continuing_education.views.utils.sdk.get_continuing_education_training_list",
        return_value={'results': [ContinuingEducationTrainingDictFactory()]}
    )

    test_case_instance.get_continuing_education_person_patcher = patch(
        "continuing_education.views.utils.sdk.get_continuing_education_person",
        return_value=ContinuingEducationPersonDictFactory(PersonFactory().uuid)
    )

    test_case_instance.get_continuing_education_training_patcher = patch(
        "continuing_education.views.utils.sdk.get_continuing_education_training",
        return_value=ContinuingEducationTrainingDictFactory()
    )

    test_case_instance.get_admission_patcher = patch(
        "continuing_education.views.utils.sdk.get_admission",
        return_value=AdmissionDictFactory(
            person_information=ContinuingEducationPersonDictFactory(PersonFactory().uuid),
            state=SUBMITTED,
            formation=ContinuingEducationTrainingDictFactory()
        )
    )

    test_case_instance.get_registration_patcher = patch(
        "continuing_education.views.utils.sdk.get_registration",
        return_value=RegistrationDictFactory(
            person_information=ContinuingEducationPersonDictFactory(PersonFactory().uuid),
            state=ACCEPTED
        )
    )

    test_case_instance.post_prospect_patcher = patch(
        "continuing_education.views.utils.sdk.post_prospect",
        return_value={'results': {}}
    )

    test_case_instance.post_admission_patcher = patch(
        "continuing_education.views.utils.sdk.post_admission",
        return_value=AdmissionDictFactory(
            uuid_arg='abcd-1234',
            person_information=ContinuingEducationPersonDictFactory(PersonFactory().uuid),
            formation=ContinuingEducationTrainingDictFactory()
        )
    )

    test_case_instance.update_admission_patcher = patch(
        "continuing_education.views.utils.sdk.update_admission",
        return_value={}
    )

    test_case_instance.update_registration_patcher = patch(
        "continuing_education.views.utils.sdk.update_registration",
        return_value={'results': {}}
    )

    test_case_instance.get_files_list_patcher = patch(
        "continuing_education.views.utils.sdk.get_files_list",
        return_value={'results': []}
    )

    test_case_instance.get_file_patcher = patch(
        "continuing_education.views.utils.sdk.get_file",
        return_value={}
    )

    test_case_instance.delete_file_patcher = patch(
        "continuing_education.views.utils.sdk.delete_file",
        return_value={'results': {}}
    )

    test_case_instance.upload_file_patcher = patch(
        "continuing_education.views.utils.sdk.upload_file",
        return_value={'results': {}}
    )

    test_case_instance.get_token_from_osis_patcher = patch(
        "continuing_education.views.utils.sdk.get_token_from_osis",
        return_value="token"
    )


def api_start_patcher(test_case_instance):
    test_case_instance.mocked_get_admission_list = test_case_instance.get_admission_list_patcher.start()
    test_case_instance.mocked_get_registration_list = test_case_instance.get_registration_list_patcher.start()
    test_case_instance.mocked_get_training_list = test_case_instance.get_continuing_education_training_list_patcher.start()
    test_case_instance.mocked_get_continuing_education_person = test_case_instance.get_continuing_education_person_patcher.start()
    test_case_instance.mocked_get_continuing_education_training = test_case_instance.get_continuing_education_training_patcher.start()
    test_case_instance.mocked_get_admission = test_case_instance.get_admission_patcher.start()
    test_case_instance.mocked_get_registration = test_case_instance.get_registration_patcher.start()
    test_case_instance.mocked_post_prospect = test_case_instance.post_prospect_patcher.start()
    test_case_instance.mocked_post_admission = test_case_instance.post_admission_patcher.start()
    test_case_instance.mocked_update_admission = test_case_instance.update_admission_patcher.start()
    test_case_instance.mocked_update_registration = test_case_instance.update_registration_patcher.start()
    test_case_instance.mocked_get_files_list = test_case_instance.get_files_list_patcher.start()
    test_case_instance.mocked_get_file = test_case_instance.get_file_patcher.start()
    test_case_instance.mocked_delete_file = test_case_instance.delete_file_patcher.start()
    test_case_instance.mocked_upload_file = test_case_instance.upload_file_patcher.start()
    test_case_instance.mocked_get_token_from_osis = test_case_instance.get_token_from_osis_patcher.start()


def api_add_cleanup_patcher(test_case_instance):
    test_case_instance.addCleanup(test_case_instance.get_admission_list_patcher.stop)
    test_case_instance.addCleanup(test_case_instance.get_registration_list_patcher.stop)
    test_case_instance.addCleanup(test_case_instance.get_continuing_education_training_list_patcher.stop)
    test_case_instance.addCleanup(test_case_instance.get_continuing_education_person_patcher.stop)
    test_case_instance.addCleanup(test_case_instance.get_admission_patcher.stop)
    test_case_instance.addCleanup(test_case_instance.get_registration_patcher.stop)
    test_case_instance.addCleanup(test_case_instance.post_prospect_patcher.stop)
    test_case_instance.addCleanup(test_case_instance.post_admission_patcher.stop)
    test_case_instance.addCleanup(test_case_instance.update_admission_patcher.stop)
    test_case_instance.addCleanup(test_case_instance.update_registration_patcher.stop)
    test_case_instance.addCleanup(test_case_instance.get_file_patcher.stop)
    test_case_instance.addCleanup(test_case_instance.get_files_list_patcher.stop)
    test_case_instance.addCleanup(test_case_instance.delete_file_patcher.stop)
    test_case_instance.addCleanup(test_case_instance.upload_file_patcher.stop)
    test_case_instance.addCleanup(test_case_instance.get_token_from_osis_patcher.stop)

