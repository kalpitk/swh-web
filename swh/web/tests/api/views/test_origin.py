# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from hypothesis import given
import pytest
from requests.utils import parse_header_links

from swh.model.model import Origin

from swh.storage.exc import StorageDBError, StorageAPIError

from swh.web.api.utils import enrich_origin_visit, enrich_origin
from swh.web.common.exc import BadInputExc
from swh.web.common.utils import reverse
from swh.web.common.origin_visits import get_origin_visits
from swh.web.tests.strategies import (
    origin, new_origin, visit_dates, new_snapshots
)


def _scroll_results(api_client, url):
    """Iterates through pages of results, and returns them all."""
    results = []

    while True:
        rv = api_client.get(url)
        assert rv.status_code == 200, rv.data
        assert rv['Content-Type'] == 'application/json'

        results.extend(rv.data)

        if 'Link' in rv:
            for link in parse_header_links(rv['Link']):
                if link['rel'] == 'next':
                    # Found link to next page of results
                    url = link['url']
                    break
            else:
                # No link with 'rel=next'
                break
        else:
            # No Link header
            break

    return results


def test_api_lookup_origin_visits_raise_error(api_client, mocker):
    mock_get_origin_visits = mocker.patch(
        'swh.web.api.views.origin.get_origin_visits')
    err_msg = 'voluntary error to check the bad request middleware.'

    mock_get_origin_visits.side_effect = BadInputExc(err_msg)

    url = reverse('api-1-origin-visits', url_args={'origin_url': 'http://foo'})
    rv = api_client.get(url)

    assert rv.status_code == 400, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert rv.data == {
        'exception': 'BadInputExc',
        'reason': err_msg
    }


def test_api_lookup_origin_visits_raise_swh_storage_error_db(api_client,
                                                             mocker):
    mock_get_origin_visits = mocker.patch(
        'swh.web.api.views.origin.get_origin_visits')
    err_msg = 'Storage exploded! Will be back online shortly!'

    mock_get_origin_visits.side_effect = StorageDBError(err_msg)

    url = reverse('api-1-origin-visits', url_args={'origin_url': 'http://foo'})
    rv = api_client.get(url)

    assert rv.status_code == 503, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert rv.data == {
        'exception': 'StorageDBError',
        'reason':
        'An unexpected error occurred in the backend: %s' % err_msg
    }


def test_api_lookup_origin_visits_raise_swh_storage_error_api(api_client,
                                                              mocker):
    mock_get_origin_visits = mocker.patch(
        'swh.web.api.views.origin.get_origin_visits')
    err_msg = 'Storage API dropped dead! Will resurrect asap!'

    mock_get_origin_visits.side_effect = StorageAPIError(err_msg)

    url = reverse(
        'api-1-origin-visits', url_args={'origin_url': 'http://foo'})
    rv = api_client.get(url)

    assert rv.status_code == 503, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert rv.data == {
        'exception': 'StorageAPIError',
        'reason':
        'An unexpected error occurred in the api backend: %s' % err_msg
    }


@given(new_origin(), visit_dates(3), new_snapshots(3))
def test_api_lookup_origin_visits(api_client, archive_data, new_origin,
                                  visit_dates, new_snapshots):

    archive_data.origin_add_one(new_origin)
    for i, visit_date in enumerate(visit_dates):
        origin_visit = archive_data.origin_visit_add(
            new_origin.url, visit_date, type='git')
        archive_data.snapshot_add([new_snapshots[i]])
        archive_data.origin_visit_update(
            new_origin.url, origin_visit.visit,
            snapshot=new_snapshots[i].id)

    all_visits = list(reversed(get_origin_visits(new_origin.to_dict())))

    for last_visit, expected_visits in (
            (None, all_visits[:2]),
            (all_visits[1]['visit'], all_visits[2:])):

        url = reverse('api-1-origin-visits',
                      url_args={'origin_url': new_origin.url},
                      query_params={'per_page': 2,
                                    'last_visit': last_visit})

        rv = api_client.get(url)

        assert rv.status_code == 200, rv.data
        assert rv['Content-Type'] == 'application/json'

        for i in range(len(expected_visits)):
            expected_visits[i] = enrich_origin_visit(
                expected_visits[i], with_origin_link=False,
                with_origin_visit_link=True, request=rv.wsgi_request)

        assert rv.data == expected_visits


@given(new_origin(), visit_dates(3), new_snapshots(3))
def test_api_lookup_origin_visits_by_id(api_client, archive_data, new_origin,
                                        visit_dates, new_snapshots):
    archive_data.origin_add_one(new_origin)
    for i, visit_date in enumerate(visit_dates):
        origin_visit = archive_data.origin_visit_add(
            new_origin.url, visit_date, type='git')
        archive_data.snapshot_add([new_snapshots[i]])
        archive_data.origin_visit_update(
            new_origin.url, origin_visit.visit,
            snapshot=new_snapshots[i].id)

    all_visits = list(reversed(get_origin_visits(new_origin.to_dict())))

    for last_visit, expected_visits in (
            (None, all_visits[:2]),
            (all_visits[1]['visit'], all_visits[2:4])):

        url = reverse('api-1-origin-visits',
                      url_args={'origin_url': new_origin.url},
                      query_params={'per_page': 2,
                                    'last_visit': last_visit})

        rv = api_client.get(url)

        assert rv.status_code == 200, rv.data
        assert rv['Content-Type'] == 'application/json'

        for i in range(len(expected_visits)):
            expected_visits[i] = enrich_origin_visit(
                expected_visits[i], with_origin_link=False,
                with_origin_visit_link=True, request=rv.wsgi_request)

        assert rv.data == expected_visits


@given(new_origin(), visit_dates(3), new_snapshots(3))
def test_api_lookup_origin_visit(api_client, archive_data, new_origin,
                                 visit_dates, new_snapshots):
    archive_data.origin_add_one(new_origin)
    for i, visit_date in enumerate(visit_dates):
        origin_visit = archive_data.origin_visit_add(
            new_origin.url, visit_date, type='git')
        visit_id = origin_visit.visit
        archive_data.snapshot_add([new_snapshots[i]])
        archive_data.origin_visit_update(
            new_origin.url, visit_id,
            snapshot=new_snapshots[i].id)
        url = reverse('api-1-origin-visit',
                      url_args={'origin_url': new_origin.url,
                                'visit_id': visit_id})

        rv = api_client.get(url)
        assert rv.status_code == 200, rv.data
        assert rv['Content-Type'] == 'application/json'

        expected_visit = archive_data.origin_visit_get_by(
            new_origin.url, visit_id)

        expected_visit = enrich_origin_visit(
            expected_visit, with_origin_link=True,
            with_origin_visit_link=False, request=rv.wsgi_request)

        assert rv.data == expected_visit


@given(new_origin())
def test_api_lookup_origin_visit_latest_no_visit(api_client, archive_data,
                                                 new_origin):
    archive_data.origin_add_one(new_origin)

    url = reverse('api-1-origin-visit-latest',
                  url_args={'origin_url': new_origin.url})

    rv = api_client.get(url)
    assert rv.status_code == 404, rv.data
    assert rv.data == {
        'exception': 'NotFoundExc',
        'reason': 'No visit for origin %s found' % new_origin.url
    }


@given(new_origin(), visit_dates(2), new_snapshots(1))
def test_api_lookup_origin_visit_latest(api_client, archive_data, new_origin,
                                        visit_dates, new_snapshots):
    archive_data.origin_add_one(new_origin)
    visit_dates.sort()
    visit_ids = []
    for i, visit_date in enumerate(visit_dates):
        origin_visit = archive_data.origin_visit_add(
            new_origin.url, visit_date, type='git')
        visit_ids.append(origin_visit.visit)

    archive_data.snapshot_add([new_snapshots[0]])
    archive_data.origin_visit_update(
        new_origin.url, visit_ids[0],
        snapshot=new_snapshots[0].id)

    url = reverse('api-1-origin-visit-latest',
                  url_args={'origin_url': new_origin.url})

    rv = api_client.get(url)

    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'

    expected_visit = archive_data.origin_visit_get_by(
        new_origin.url, visit_ids[1])

    expected_visit = enrich_origin_visit(
            expected_visit, with_origin_link=True,
            with_origin_visit_link=False, request=rv.wsgi_request)

    assert rv.data == expected_visit


@given(new_origin(), visit_dates(2), new_snapshots(1))
def test_api_lookup_origin_visit_latest_with_snapshot(api_client, archive_data,
                                                      new_origin, visit_dates,
                                                      new_snapshots):
    archive_data.origin_add_one(new_origin)
    visit_dates.sort()
    visit_ids = []
    for i, visit_date in enumerate(visit_dates):
        origin_visit = archive_data.origin_visit_add(
            new_origin.url, visit_date, type='git')
        visit_ids.append(origin_visit.visit)

    archive_data.snapshot_add([new_snapshots[0]])
    archive_data.origin_visit_update(
        new_origin.url, visit_ids[0],
        snapshot=new_snapshots[0].id)

    url = reverse('api-1-origin-visit-latest',
                  url_args={'origin_url': new_origin.url},
                  query_params={'require_snapshot': True})

    rv = api_client.get(url)

    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'

    expected_visit = archive_data.origin_visit_get_by(
        new_origin.url, visit_ids[0])

    expected_visit = enrich_origin_visit(
            expected_visit, with_origin_link=True,
            with_origin_visit_link=False, request=rv.wsgi_request)

    assert rv.data == expected_visit


@given(origin())
def test_api_lookup_origin_visit_not_found(api_client, origin):

    all_visits = list(reversed(get_origin_visits(origin)))

    max_visit_id = max([v['visit'] for v in all_visits])

    url = reverse('api-1-origin-visit',
                  url_args={'origin_url': origin['url'],
                            'visit_id': max_visit_id + 1})

    rv = api_client.get(url)

    assert rv.status_code == 404, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert rv.data == {
        'exception': 'NotFoundExc',
        'reason': 'Origin %s or its visit with id %s not found!' %
        (origin['url'], max_visit_id+1)
    }


def test_api_origins(api_client, archive_data):
    origins = list(archive_data.origin_get_range(0, 10000))
    origin_urls = {origin['url'] for origin in origins}

    # Get only one
    url = reverse('api-1-origins',
                  query_params={'origin_count': 1})
    rv = api_client.get(url)
    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert len(rv.data) == 1
    assert {origin['url'] for origin in rv.data} <= origin_urls

    # Get all
    url = reverse('api-1-origins',
                  query_params={'origin_count': len(origins)})
    rv = api_client.get(url)
    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert len(rv.data) == len(origins)
    assert {origin['url'] for origin in rv.data} == origin_urls

    # Get "all + 10"
    url = reverse('api-1-origins',
                  query_params={'origin_count': len(origins)+10})
    rv = api_client.get(url)
    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert len(rv.data) == len(origins)
    assert {origin['url'] for origin in rv.data} == origin_urls


@pytest.mark.parametrize('origin_count', [1, 2, 10, 100])
def test_api_origins_scroll(api_client, archive_data, origin_count):
    origins = list(archive_data.origin_get_range(0, 10000))
    origin_urls = {origin['url'] for origin in origins}

    url = reverse('api-1-origins',
                  query_params={'origin_count': origin_count})

    results = _scroll_results(api_client, url)

    assert len(results) == len(origins)
    assert {origin['url'] for origin in results} == origin_urls


@given(origin())
def test_api_origin_by_url(api_client, archive_data, origin):
    url = reverse('api-1-origin',
                  url_args={'origin_url': origin['url']})
    rv = api_client.get(url)

    expected_origin = archive_data.origin_get(origin)

    expected_origin = enrich_origin(expected_origin, rv.wsgi_request)

    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert rv.data == expected_origin


@given(new_origin())
def test_api_origin_not_found(api_client, new_origin):

    url = reverse('api-1-origin',
                  url_args={'origin_url': new_origin.url})
    rv = api_client.get(url)

    assert rv.status_code == 404, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert rv.data == {
        'exception': 'NotFoundExc',
        'reason': 'Origin with url %s not found!' % new_origin.url
    }


@pytest.mark.parametrize('backend', ['swh-search', 'swh-storage'])
def test_api_origin_search(api_client, mocker, backend):
    if backend != 'swh-search':
        # equivalent to not configuring search in the config
        mocker.patch('swh.web.common.service.search', None)

    expected_origins = {
        'https://github.com/wcoder/highlightjs-line-numbers.js',
        'https://github.com/memononen/libtess2',
    }

    # Search for 'github.com', get only one
    url = reverse('api-1-origin-search',
                  url_args={'url_pattern': 'github.com'},
                  query_params={'limit': 1})
    rv = api_client.get(url)
    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert len(rv.data) == 1
    assert {origin['url'] for origin in rv.data} <= expected_origins

    # Search for 'github.com', get all
    url = reverse('api-1-origin-search',
                  url_args={'url_pattern': 'github.com'},
                  query_params={'limit': 2})
    rv = api_client.get(url)
    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert {origin['url'] for origin in rv.data} == expected_origins

    # Search for 'github.com', get more than available
    url = reverse('api-1-origin-search',
                  url_args={'url_pattern': 'github.com'},
                  query_params={'limit': 10})
    rv = api_client.get(url)
    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert {origin['url'] for origin in rv.data} == expected_origins


@pytest.mark.parametrize('backend', ['swh-search', 'swh-storage'])
def test_api_origin_search_words(api_client, mocker, backend):
    if backend != 'swh-search':
        # equivalent to not configuring search in the config
        mocker.patch('swh.web.common.service.search', None)

    expected_origins = {
        'https://github.com/wcoder/highlightjs-line-numbers.js',
        'https://github.com/memononen/libtess2',
    }

    url = reverse('api-1-origin-search',
                  url_args={'url_pattern': 'github com'},
                  query_params={'limit': 2})
    rv = api_client.get(url)
    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert {origin['url'] for origin in rv.data} == expected_origins

    url = reverse('api-1-origin-search',
                  url_args={'url_pattern': 'com github'},
                  query_params={'limit': 2})
    rv = api_client.get(url)
    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert {origin['url'] for origin in rv.data} == expected_origins

    url = reverse('api-1-origin-search',
                  url_args={'url_pattern': 'memononen libtess2'},
                  query_params={'limit': 2})
    rv = api_client.get(url)
    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert len(rv.data) == 1
    assert {origin['url'] for origin in rv.data} \
        == {'https://github.com/memononen/libtess2'}

    url = reverse('api-1-origin-search',
                  url_args={'url_pattern': 'libtess2 memononen'},
                  query_params={'limit': 2})
    rv = api_client.get(url)
    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert len(rv.data) == 1
    assert {origin['url'] for origin in rv.data} \
        == {'https://github.com/memononen/libtess2'}


@pytest.mark.parametrize('backend', ['swh-search', 'swh-storage'])
@pytest.mark.parametrize('limit', [1, 2, 3, 10])
def test_api_origin_search_scroll(
        api_client, archive_data, mocker, limit, backend):

    if backend != 'swh-search':
        # equivalent to not configuring search in the config
        mocker.patch('swh.web.common.service.search', None)

    expected_origins = {
        'https://github.com/wcoder/highlightjs-line-numbers.js',
        'https://github.com/memononen/libtess2',
    }

    url = reverse('api-1-origin-search',
                  url_args={'url_pattern': 'github.com'},
                  query_params={'limit': limit})

    results = _scroll_results(api_client, url)

    assert {origin['url'] for origin in results} == expected_origins


@pytest.mark.parametrize('backend', ['swh-search', 'swh-storage'])
def test_api_origin_search_limit(
        api_client, archive_data, tests_data, mocker, backend):
    if backend == 'swh-search':
        tests_data['search'].origin_update([
            {'url': 'http://foobar/{}'.format(i)}
            for i in range(2000)
        ])
    else:
        # equivalent to not configuring search in the config
        mocker.patch('swh.web.common.service.search', None)

        archive_data.origin_add([
            Origin(url='http://foobar/{}'.format(i))
            for i in range(2000)
        ])

    url = reverse('api-1-origin-search',
                  url_args={'url_pattern': 'foobar'},
                  query_params={'limit': 1050})
    rv = api_client.get(url)
    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert len(rv.data) == 1000


@given(origin())
def test_api_origin_metadata_search(api_client, mocker, origin):
    mock_idx_storage = mocker.patch('swh.web.common.service.idx_storage')
    oimsft = mock_idx_storage.origin_intrinsic_metadata_search_fulltext
    oimsft.side_effect = lambda conjunction, limit: [{
        'from_revision': (
            b'p&\xb7\xc1\xa2\xafVR\x1e\x95\x1c\x01\xed '
            b'\xf2U\xfa\x05B8'),
        'metadata': {'author': 'Jane Doe'},
        'id': origin['url'],
        'tool': {
            'configuration': {
                'context': ['NpmMapping', 'CodemetaMapping'],
                'type': 'local'
            },
            'id': 3,
            'name': 'swh-metadata-detector',
            'version': '0.0.1'
        }
    }]

    url = reverse('api-1-origin-metadata-search',
                  query_params={'fulltext': 'Jane Doe'})
    rv = api_client.get(url)

    assert rv.status_code == 200, rv.content
    assert rv['Content-Type'] == 'application/json'
    expected_data = [{
        'url': origin['url'],
        'metadata': {
            'metadata': {'author': 'Jane Doe'},
            'from_revision': (
                '7026b7c1a2af56521e951c01ed20f255fa054238'),
            'tool': {
                'configuration': {
                    'context': ['NpmMapping', 'CodemetaMapping'],
                    'type': 'local'
                },
                'id': 3,
                'name': 'swh-metadata-detector',
                'version': '0.0.1',
            }
        }
    }]

    assert rv.data == expected_data
    oimsft.assert_called_with(conjunction=['Jane Doe'], limit=70)


@given(origin())
def test_api_origin_metadata_search_limit(api_client, mocker, origin):
    mock_idx_storage = mocker.patch('swh.web.common.service.idx_storage')
    oimsft = mock_idx_storage.origin_intrinsic_metadata_search_fulltext

    oimsft.side_effect = lambda conjunction, limit: [{
        'from_revision': (
            b'p&\xb7\xc1\xa2\xafVR\x1e\x95\x1c\x01\xed '
            b'\xf2U\xfa\x05B8'),
        'metadata': {'author': 'Jane Doe'},
        'id': origin['url'],
        'tool': {
            'configuration': {
                'context': ['NpmMapping', 'CodemetaMapping'],
                'type': 'local'
            },
            'id': 3,
            'name': 'swh-metadata-detector',
            'version': '0.0.1'
        }
    }]

    url = reverse('api-1-origin-metadata-search',
                  query_params={'fulltext': 'Jane Doe'})
    rv = api_client.get(url)

    assert rv.status_code == 200, rv.content
    assert rv['Content-Type'] == 'application/json'
    assert len(rv.data) == 1
    oimsft.assert_called_with(conjunction=['Jane Doe'], limit=70)

    url = reverse('api-1-origin-metadata-search',
                  query_params={'fulltext': 'Jane Doe',
                                'limit': 10})
    rv = api_client.get(url)

    assert rv.status_code == 200, rv.content
    assert rv['Content-Type'] == 'application/json'
    assert len(rv.data) == 1
    oimsft.assert_called_with(conjunction=['Jane Doe'], limit=10)

    url = reverse('api-1-origin-metadata-search',
                  query_params={'fulltext': 'Jane Doe',
                                'limit': 987})
    rv = api_client.get(url)

    assert rv.status_code == 200, rv.content
    assert rv['Content-Type'] == 'application/json'
    assert len(rv.data) == 1
    oimsft.assert_called_with(conjunction=['Jane Doe'], limit=100)


@given(origin())
def test_api_origin_intrinsic_metadata(api_client, mocker, origin):
    mock_idx_storage = mocker.patch('swh.web.common.service.idx_storage')
    oimg = mock_idx_storage.origin_intrinsic_metadata_get
    oimg.side_effect = lambda origin_urls: [{
        'from_revision': (
            b'p&\xb7\xc1\xa2\xafVR\x1e\x95\x1c\x01\xed '
            b'\xf2U\xfa\x05B8'),
        'metadata': {'author': 'Jane Doe'},
        'id': origin['url'],
        'tool': {
            'configuration': {
                'context': ['NpmMapping', 'CodemetaMapping'],
                'type': 'local'
            },
            'id': 3,
            'name': 'swh-metadata-detector',
            'version': '0.0.1'
        }
    }]

    url = reverse('api-origin-intrinsic-metadata',
                  url_args={'origin_url': origin['url']})
    rv = api_client.get(url)

    oimg.assert_called_once_with([origin['url']])
    assert rv.status_code == 200, rv.content
    assert rv['Content-Type'] == 'application/json'
    expected_data = {'author': 'Jane Doe'}
    assert rv.data == expected_data


def test_api_origin_metadata_search_invalid(api_client, mocker):
    mock_idx_storage = mocker.patch('swh.web.common.service.idx_storage')
    url = reverse('api-1-origin-metadata-search')
    rv = api_client.get(url)

    assert rv.status_code == 400, rv.content
    mock_idx_storage.assert_not_called()
