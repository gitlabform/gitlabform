from unittest.mock import MagicMock, patch

from gitlabform.processors.defining_keys import Key
from gitlabform.processors.multiple_entities_processor import MultipleEntitiesProcessor


class TestMultipleEntitiesProcessor:
    def setup_method(self):
        self.gitlab = MagicMock()
        self.list_method = MagicMock(return_value=[])
        self.add_method = MagicMock()
        self.delete_method = MagicMock()
        self.edit_method = MagicMock()
        with patch("gitlabform.processors.abstract_processor.GitlabWrapper"):
            self.processor = MultipleEntitiesProcessor(
                configuration_name="entities",
                gitlab=self.gitlab,
                list_method_name=self.list_method,
                add_method_name=self.add_method,
                delete_method_name=self.delete_method,
                edit_method_name=self.edit_method,
                defining=Key("name"),
                required_to_create_or_update=Key("name"),
            )

    def test_delete_true_on_entity_absent_from_gitlab_does_not_create_it(self):
        configuration = {"entities": {"ghost": {"name": "ghost", "delete": True}}}

        self.processor._process_configuration("group/x", configuration)

        self.add_method.assert_not_called()
        self.delete_method.assert_not_called()
