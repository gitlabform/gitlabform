gitlab_rails['initial_root_password']='mK9JnG7jwYdFcBNoQ3W3'
registry['enable']=false
prometheus_monitoring['enable']=false
gitlab_rails['initial_license_file']='/etc/gitlab/Gitlab.gitlab-license'
gitlab_kas['enable']=false
gitlab_rails['omniauth_enabled'] = true
gitlab_rails['omniauth_allow_single_sign_on'] = ['saml']
gitlab_rails['omniauth_block_auto_created_users'] = false
gitlab_rails['omniauth_auto_link_saml_user'] = true
gitlab_rails['omniauth_providers'] = [
  {
    name: 'saml',
    args: {
             assertion_consumer_service_url: 'http://localhost/users/auth/saml/callback',
             idp_cert_fingerprint: '11:9B:9E:02:79:59:CD:B7:C6:62:CF:D0:75:D9:E2:EF:38:4E:44:5F',
             idp_sso_target_url: 'http://localhost:8080/simplesaml/saml2/idp/SSOService.php',
             issuer: 'http://app.example.com',
             name_identifier_format: 'urn:oasis:names:tc:SAML:2.0:nameid-format:persistent'
           },
    label: 'SAML Login'
  }
]