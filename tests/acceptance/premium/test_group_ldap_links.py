import pytest

from tests.acceptance import run_gitlabform
from gitlabform.gitlab import AccessLevel
from gitlab.exceptions import GitlabListError

pytestmark = pytest.mark.requires_license


class TestGroupLDAPLinks:
    def test__add_ldap_links(self, gl, group):
        """Test adding LDAP links to a group."""

        # Verify that there are no existing LDAP links
        # GitLab API returns 404 if there are no LDAP links configured.
        # That's why expecting GitlabListError when trying to get the existing links.
        with pytest.raises(GitlabListError):
            group.ldap_group_links.list(get_all=True)

        # Add LDAP links to the group using basic configuration
        add_ldap_link = f"""
        projects_and_groups:
          {group.full_path}/*:              
            group_ldap_links: 
              devops_users:                                 
                provider: LDAP Main
                cn: devops
                group_access: maintainer
        """
        run_gitlabform(add_ldap_link, group)

        # Verify that the LDAP link was created
        refreshed_group = gl.groups.get(group.id)
        ldap_links = refreshed_group.ldap_group_links.list(get_all=True)
        assert len(ldap_links) == 1
        assert ldap_links[0].provider == "LDAP Main"
        assert ldap_links[0].cn == "devops"
        assert ldap_links[0].group_access == AccessLevel.get_value("maintainer")
