from django.forms.models import model_to_dict
from django.db.models import Model
from rest_framework.utils.encoders import JSONEncoder as RestJSONEncoder
import json


class JSONEncoder(RestJSONEncoder):

    def default(self, obj):
        if isinstance(obj, Model):
            return model_to_dict(obj)

        ex = getattr(obj, '_excludes', {})
        customs = getattr(obj, '_customs', {})
        if ex or customs:
            vals = customs.copy()
            vals.update(getattr(obj, '__dict__', {}))
            return dict([(k, v) for k, v in vals.items()
                         if k not in ex and not k.startswith('_') and v])
        return super(JSONEncoder, self).default(obj)

    @classmethod
    def to_json(cls, obj, *args, **kwargs):
        return json.dumps(obj, cls=cls, *args, **kwargs)

    @classmethod
    def from_json(cls, jsonstr,  *args, **kwargs):
        return json.loads(jsonstr, *args, **kwargs)


to_json = JSONEncoder.to_json
from_json = JSONEncoder.from_json
