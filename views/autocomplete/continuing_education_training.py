import json

from dal import autocomplete
from django import http

from continuing_education.views.utils.sdk import get_continuing_education_training_list


class ContinuingEducationTrainingAutocomplete(autocomplete.Select2ListView):

    def get(self, request, *args, **kwargs):
        return http.HttpResponse(json.dumps({
            'results': [
                {
                    'id': training['uuid'],
                    'text': "{} - {}".format(
                        training['education_group']['acronym'],
                        training['education_group']['title']
                    )
                }
                for training in get_continuing_education_training_list(
                    search=self.q,
                    active=True
                )['results']
            ]
        }), content_type='application/json')
