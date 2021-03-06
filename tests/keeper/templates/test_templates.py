from squid_py.keeper.templates.template_manager import TemplateStoreManager
from tests.resources.tiers import e2e_test

template_store_manager = TemplateStoreManager('TemplateStoreManager')


@e2e_test
def test_template():
    assert template_store_manager.get_num_templates() == 1
