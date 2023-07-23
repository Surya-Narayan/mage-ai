import urllib.parse
from mage_ai.api.errors import ApiError
from mage_ai.api.resources.GenericResource import GenericResource
from mage_ai.data_preparation.models.custom_templates.constants import (
    DIRECTORY_FOR_BLOCK_TEMPLATES,
)
from mage_ai.data_preparation.models.custom_templates.custom_block_template import (
    CustomBlockTemplate,
)
from mage_ai.data_preparation.models.custom_templates.utils import (
    flatten_files,
    get_templates,
    group_and_hydrate_files,
)
from mage_ai.data_preparation.templates.template import fetch_template_source
from mage_ai.shared.hash import ignore_keys

OBJECT_TYPE_KEY = 'object_type'


class CustomTemplateResource(GenericResource):
    @classmethod
    def collection(self, query, meta, user, **kwargs):
        object_type = query.get(OBJECT_TYPE_KEY, [None])
        if object_type:
            object_type = object_type[0]

        templates = []

        if DIRECTORY_FOR_BLOCK_TEMPLATES == object_type:
            file_dicts = get_templates(DIRECTORY_FOR_BLOCK_TEMPLATES)
            file_dicts_flat = flatten_files(file_dicts)
            templates = group_and_hydrate_files(file_dicts_flat, CustomBlockTemplate)

        return self.build_result_set(
            templates,
            user,
            **kwargs,
        )

    @classmethod
    def create(self, payload, user, **kwargs):
        custom_template = None

        if DIRECTORY_FOR_BLOCK_TEMPLATES == payload.get(OBJECT_TYPE_KEY):
            template_uuid = payload.get('template_uuid')
            custom_template = CustomBlockTemplate.load(template_uuid=template_uuid)

            if not custom_template:
                custom_template = CustomBlockTemplate(**ignore_keys(payload, [
                    'uuid',
                    OBJECT_TYPE_KEY,
                ]))
                if user:
                    custom_template.user = dict(
                        username=user.username,
                    )

                custom_template.content = fetch_template_source(
                    custom_template.block_type,
                    payload.get('config', {}),
                    language=custom_template.language,
                )

                custom_template.save()

        if custom_template:
            return self(custom_template, user, **kwargs)

    @classmethod
    def member(self, pk, user, **kwargs):
        query = kwargs.get('query', {})
        object_type = query.get(OBJECT_TYPE_KEY, [None])
        if object_type:
            object_type = object_type[0]

        template_uuid = urllib.parse.unquote(pk)

        try:
            if DIRECTORY_FOR_BLOCK_TEMPLATES == object_type:
                return self(CustomBlockTemplate.load(template_uuid=template_uuid), user, **kwargs)
        except Exception as err:
            print(f'[WARNING] CustomTemplateResource.member: {err}')
            raise ApiError(ApiError.RESOURCE_NOT_FOUND)

    def delete(self, **kwargs):
        self.model.delete

    def update(self, payload, **kwargs):
        for key, value in ignore_keys(payload, [
            'uuid',
            OBJECT_TYPE_KEY,
        ]).items():
            setattr(self.model, key, value)
        self.model.save()