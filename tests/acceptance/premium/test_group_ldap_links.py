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

        # Test 1: Add LDAP links to the group using basic configuration
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

        # Test 2: Add LDAP link to group using 'filter' instead of 'cn'
        add_ldap_link = f"""
        projects_and_groups:
          {group.full_path}/*:              
            group_ldap_links: 
              security_users:                                 
                provider: LDAP Main
                filter: (devType=security)
                group_access: developer
        """
        run_gitlabform(add_ldap_link, group)

        # Verify that the LDAP link was created
        refreshed_group = gl.groups.get(group.id)
        ldap_links = refreshed_group.ldap_group_links.list(get_all=True)
        assert len(ldap_links) == 2
        assert ldap_links[1].provider == "LDAP Main"
        assert ldap_links[1].filter == "(devType=security)"
        assert ldap_links[1].group_access == AccessLevel.get_value("developer")

    def test__update_ldap_links(self, gl, group):
        """Test updaing LDAP links of a group."""

        # Verify group has 2 ldap links - last state of the group in previous test
        assert len(group.ldap_group_links.list()) == 2

        # Test 1: Update the 2 ldap links that were added to the group in previous test
        update_group_ldap_settings = f"""
        projects_and_groups:
          {group.full_path}/*:              
            group_ldap_links: 
              devops_users:                                 
                provider: LDAP Main
                cn: devops
                group_access: developer  # <-- Changed from 'maintainer'
              security_users:                                 
                provider: LDAP Main
                filter: (devType=security)
                group_access: reporter  # <-- Changed from 'developer'
        """
        run_gitlabform(update_group_ldap_settings, group)
        # Verify that the LDAP link was updated
        refreshed_group = gl.groups.get(group.id)
        ldap_links = refreshed_group.ldap_group_links.list(get_all=True)
        assert len(ldap_links) == 2

        assert ldap_links[0].provider == "LDAP Main"
        assert ldap_links[0].cn == "devops"
        assert ldap_links[0].group_access == AccessLevel.get_value("developer")

        assert ldap_links[1].provider == "LDAP Main"
        assert ldap_links[1].filter == "(devType=security)"
        assert ldap_links[1].group_access == AccessLevel.get_value("reporter")

    def test__enforce_ldap_links(self, gl, group):
        """Test enforce mode for LDAP links config of a group."""

        # Verify group has 2 ldap links - last state of the group in previous test
        assert len(group.ldap_group_links.list()) == 2

        # Test: Previous test had configured 2 ldap links: devops_users, security_users
        # Enable enforce mode and skip security_users in the config
        # This should result in security_users being removed
        enforce_ldap_settings = f"""
        projects_and_groups:
          {group.full_path}/*:              
            group_ldap_links:
              enforce: true 
              devops_users:                                 
                provider: LDAP Main
                cn: devops
                group_access: developer
        """
        run_gitlabform(enforce_ldap_settings, group)

        # Verify result
        refreshed_group = gl.groups.get(group.id)
        ldap_links = refreshed_group.ldap_group_links.list(get_all=True)
        assert len(ldap_links) == 1

        assert ldap_links[0].provider == "LDAP Main"
        assert ldap_links[0].cn == "devops"
        assert ldap_links[0].group_access == AccessLevel.get_value("developer")
