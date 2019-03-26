import json

from dal import autocomplete
from django import http

from continuing_education.views.api import get_continuing_education_training_list


class ContinuingEducationTrainingAutocomplete(autocomplete.Select2ListView):

    def get(self, request, *args, **kwargs):
        return http.HttpResponse(json.dumps({
            'results': [
                {'id': training['uuid'], 'text': training['education_group']['acronym']}
                for training in get_continuing_education_training_list(
                    search=self.q,
                )
            ]
        }), content_type='application/json')
