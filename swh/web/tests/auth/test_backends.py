# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timedelta

from django.contrib.auth import authenticate, get_backends

import pytest

from django.conf import settings

from rest_framework.exceptions import AuthenticationFailed

from swh.web.auth.backends import OIDCBearerTokenAuthentication
from swh.web.auth.models import OIDCUser
from swh.web.common.utils import reverse

from . import sample_data
from .keycloak_mock import mock_keycloak


def _authenticate_user(request_factory):
    request = request_factory.get(reverse('oidc-login-complete'))

    return authenticate(request=request,
                        code='some-code',
                        code_verifier='some-code-verifier',
                        redirect_uri='https://localhost:5004')


def _check_authenticated_user(user):
    userinfo = sample_data.userinfo
    assert user is not None
    assert isinstance(user, OIDCUser)
    assert user.id != 0
    assert user.username == userinfo['preferred_username']
    assert user.password == ''
    assert user.first_name == userinfo['given_name']
    assert user.last_name == userinfo['family_name']
    assert user.email == userinfo['email']
    assert user.is_staff == ('/staff' in userinfo['groups'])
    assert user.sub == userinfo['sub']


@pytest.mark.django_db
def test_oidc_code_pkce_auth_backend_success(mocker, request_factory):
    kc_oidc_mock = mock_keycloak(mocker)
    oidc_profile = sample_data.oidc_profile
    user = _authenticate_user(request_factory)

    _check_authenticated_user(user)

    decoded_token = kc_oidc_mock.decode_token(
        sample_data.oidc_profile['access_token'])
    auth_datetime = datetime.fromtimestamp(decoded_token['auth_time'])

    access_expiration = (
        auth_datetime + timedelta(seconds=oidc_profile['expires_in']))
    refresh_expiration = (
        auth_datetime + timedelta(seconds=oidc_profile['refresh_expires_in']))

    assert user.access_token == oidc_profile['access_token']
    assert user.access_expiration == access_expiration
    assert user.id_token == oidc_profile['id_token']
    assert user.refresh_token == oidc_profile['refresh_token']
    assert user.refresh_expiration == refresh_expiration
    assert user.scope == oidc_profile['scope']
    assert user.session_state == oidc_profile['session_state']

    backend_path = 'swh.web.auth.backends.OIDCAuthorizationCodePKCEBackend'
    assert user.backend == backend_path
    backend_idx = settings.AUTHENTICATION_BACKENDS.index(backend_path)
    assert get_backends()[backend_idx].get_user(user.id) == user


@pytest.mark.django_db
def test_oidc_code_pkce_auth_backend_failure(mocker, request_factory):
    mock_keycloak(mocker, auth_success=False)

    user = _authenticate_user(request_factory)

    assert user is None


@pytest.mark.django_db
def test_drf_oidc_bearer_token_auth_backend_success(mocker,
                                                    api_request_factory):
    url = reverse('api-1-stat-counters')
    drf_auth_backend = OIDCBearerTokenAuthentication()

    kc_oidc_mock = mock_keycloak(mocker)

    access_token = sample_data.oidc_profile['access_token']

    request = api_request_factory.get(
        url, HTTP_AUTHORIZATION=f"Bearer {access_token}")

    # first authentication
    user, _ = drf_auth_backend.authenticate(request)
    _check_authenticated_user(user)
    # oidc_profile is not filled when authenticating through bearer token
    assert hasattr(user, 'access_token') and user.access_token is None

    # second authentication, should fetch userinfo from cache
    # until token expires
    user, _ = drf_auth_backend.authenticate(request)
    _check_authenticated_user(user)
    assert hasattr(user, 'access_token') and user.access_token is None

    # check user request to keycloak has been sent only once
    kc_oidc_mock.userinfo.assert_called_once_with(access_token)


@pytest.mark.django_db
def test_drf_oidc_bearer_token_auth_backend_failure(mocker,
                                                    api_request_factory):

    url = reverse('api-1-stat-counters')
    drf_auth_backend = OIDCBearerTokenAuthentication()

    # simulate a failed authentication with a bearer token in expected format
    mock_keycloak(mocker, auth_success=False)

    access_token = sample_data.oidc_profile['access_token']

    request = api_request_factory.get(
        url, HTTP_AUTHORIZATION=f"Bearer {access_token}")

    with pytest.raises(AuthenticationFailed):
        drf_auth_backend.authenticate(request)

    # simulate a failed authentication with an invalid bearer token format
    mock_keycloak(mocker)

    request = api_request_factory.get(
        url, HTTP_AUTHORIZATION=f"Bearer invalid-token-format")

    with pytest.raises(AuthenticationFailed):
        drf_auth_backend.authenticate(request)


def test_drf_oidc_auth_invalid_or_missing_auth_type(api_request_factory):

    url = reverse('api-1-stat-counters')
    drf_auth_backend = OIDCBearerTokenAuthentication()

    access_token = sample_data.oidc_profile['access_token']

    # Invalid authorization type
    request = api_request_factory.get(
        url, HTTP_AUTHORIZATION=f"Foo token")

    with pytest.raises(AuthenticationFailed):
        drf_auth_backend.authenticate(request)

    # Missing authorization type
    request = api_request_factory.get(
        url, HTTP_AUTHORIZATION=f"{access_token}")

    with pytest.raises(AuthenticationFailed):
        drf_auth_backend.authenticate(request)
