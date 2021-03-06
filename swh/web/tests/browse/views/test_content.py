# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.utils.html import escape

from hypothesis import given

from swh.web.browse.utils import (
    get_mimetype_and_encoding_for_content, prepare_content_for_display,
    _re_encode_content
)
from swh.web.common.exc import NotFoundExc
from swh.web.common.utils import reverse, get_swh_persistent_id
from swh.web.common.utils import gen_path_info
from swh.web.tests.django_asserts import (
    assert_contains, assert_not_contains, assert_template_used
)
from swh.web.tests.strategies import (
    content, content_text_non_utf8, content_text_no_highlight,
    content_image_type, content_text, invalid_sha1, unknown_content,
    content_utf8_detected_as_binary
)


@given(content_text())
def test_content_view_text(client, archive_data, content):
    sha1_git = content['sha1_git']

    url = reverse('browse-content',
                  url_args={'query_string': content['sha1']},
                  query_params={'path': content['path']})

    url_raw = reverse('browse-content-raw',
                      url_args={'query_string': content['sha1']})

    resp = client.get(url)

    content_display = _process_content_for_display(archive_data, content)
    mimetype = content_display['mimetype']

    assert resp.status_code == 200
    assert_template_used(resp, 'browse/content.html')

    if mimetype.startswith('text/'):
        assert_contains(resp, '<code class="%s">' %
                        content_display['language'])
        assert_contains(resp, escape(content_display['content_data']))
    assert_contains(resp, url_raw)

    swh_cnt_id = get_swh_persistent_id('content', sha1_git)
    swh_cnt_id_url = reverse('browse-swh-id',
                             url_args={'swh_id': swh_cnt_id})
    assert_contains(resp, swh_cnt_id)
    assert_contains(resp, swh_cnt_id_url)


@given(content_text_no_highlight())
def test_content_view_text_no_highlight(client, archive_data, content):
    sha1_git = content['sha1_git']

    url = reverse('browse-content',
                  url_args={'query_string': content['sha1']})

    url_raw = reverse('browse-content-raw',
                      url_args={'query_string': content['sha1']})

    resp = client.get(url)

    content_display = _process_content_for_display(archive_data, content)

    assert resp.status_code == 200
    assert_template_used(resp, 'browse/content.html')

    assert_contains(resp, '<code class="nohighlight">')
    assert_contains(resp, escape(content_display['content_data']))
    assert_contains(resp, url_raw)

    swh_cnt_id = get_swh_persistent_id('content', sha1_git)
    swh_cnt_id_url = reverse('browse-swh-id',
                             url_args={'swh_id': swh_cnt_id})

    assert_contains(resp, swh_cnt_id)
    assert_contains(resp, swh_cnt_id_url)


@given(content_text_non_utf8())
def test_content_view_no_utf8_text(client, archive_data, content):
    sha1_git = content['sha1_git']

    url = reverse('browse-content',
                  url_args={'query_string': content['sha1']})

    resp = client.get(url)

    content_display = _process_content_for_display(archive_data, content)

    assert resp.status_code == 200
    assert_template_used(resp, 'browse/content.html')
    swh_cnt_id = get_swh_persistent_id('content', sha1_git)
    swh_cnt_id_url = reverse('browse-swh-id',
                             url_args={'swh_id': swh_cnt_id})
    assert_contains(resp, swh_cnt_id_url)
    assert_contains(resp, escape(content_display['content_data']))


@given(content_image_type())
def test_content_view_image(client, archive_data, content):
    url = reverse('browse-content',
                  url_args={'query_string': content['sha1']})

    url_raw = reverse('browse-content-raw',
                      url_args={'query_string': content['sha1']})

    resp = client.get(url)

    content_display = _process_content_for_display(archive_data, content)
    mimetype = content_display['mimetype']
    content_data = content_display['content_data']

    assert resp.status_code == 200
    assert_template_used(resp, 'browse/content.html')
    assert_contains(resp, '<img src="data:%s;base64,%s"/>'
                    % (mimetype, content_data))
    assert_contains(resp, url_raw)


@given(content_text())
def test_content_view_text_with_path(client, archive_data, content):
    path = content['path']

    url = reverse('browse-content',
                  url_args={'query_string': content['sha1']},
                  query_params={'path': path})

    resp = client.get(url)
    assert resp.status_code == 200
    assert_template_used(resp, 'browse/content.html')

    assert_contains(resp, '<nav class="bread-crumbs')

    content_display = _process_content_for_display(archive_data, content)
    mimetype = content_display['mimetype']

    if mimetype.startswith('text/'):
        hljs_language = content['hljs_language']
        assert_contains(resp, '<code class="%s">' % hljs_language)
        assert_contains(resp, escape(content_display['content_data']))

    split_path = path.split('/')

    root_dir_sha1 = split_path[0]
    filename = split_path[-1]
    path = path.replace(root_dir_sha1 + '/', '').replace(filename, '')

    path_info = gen_path_info(path)

    root_dir_url = reverse('browse-directory',
                           url_args={'sha1_git': root_dir_sha1})

    assert_contains(resp, '<li class="swh-path">',
                    count=len(path_info)+1)

    assert_contains(resp, '<a href="' + root_dir_url + '">' +
                    root_dir_sha1[:7] + '</a>')

    for p in path_info:
        dir_url = reverse('browse-directory',
                          url_args={'sha1_git': root_dir_sha1,
                                    'path': p['path']})
        assert_contains(resp, '<a href="' + dir_url + '">' +
                        p['name'] + '</a>')

    assert_contains(resp, '<li>' + filename + '</li>')

    url_raw = reverse('browse-content-raw',
                      url_args={'query_string': content['sha1']},
                      query_params={'filename': filename})
    assert_contains(resp, url_raw)

    url = reverse('browse-content',
                  url_args={'query_string': content['sha1']},
                  query_params={'path': filename})

    resp = client.get(url)
    assert resp.status_code == 200
    assert_template_used(resp, 'browse/content.html')

    assert_not_contains(resp, '<nav class="bread-crumbs')

    invalid_path = '%s/foo/bar/baz' % root_dir_sha1
    url = reverse('browse-content',
                  url_args={'query_string': content['sha1']},
                  query_params={'path': invalid_path})
    resp = client.get(url)
    assert resp.status_code == 404


@given(content_text())
def test_content_raw_text(client, archive_data, content):
    url = reverse('browse-content-raw',
                  url_args={'query_string': content['sha1']})

    resp = client.get(url)

    content_data = archive_data.content_get(content['sha1'])['data']

    assert resp.status_code == 200
    assert resp['Content-Type'] == 'text/plain'
    assert resp['Content-disposition'] == ('filename=%s_%s' %
                                           ('sha1', content['sha1']))
    assert resp.content == content_data

    filename = content['path'].split('/')[-1]

    url = reverse('browse-content-raw',
                  url_args={'query_string': content['sha1']},
                  query_params={'filename': filename})

    resp = client.get(url)

    assert resp.status_code == 200
    assert resp['Content-Type'] == 'text/plain'
    assert resp['Content-disposition'] == 'filename=%s' % filename
    assert resp.content == content_data


@given(content_text_non_utf8())
def test_content_raw_no_utf8_text(client, content):
    url = reverse('browse-content-raw',
                  url_args={'query_string': content['sha1']})

    resp = client.get(url)
    assert resp.status_code == 200
    _, encoding = get_mimetype_and_encoding_for_content(resp.content)
    assert encoding == content['encoding']


@given(content_image_type())
def test_content_raw_bin(client, archive_data, content):
    url = reverse('browse-content-raw',
                  url_args={'query_string': content['sha1']})

    resp = client.get(url)

    filename = content['path'].split('/')[-1]
    content_data = archive_data.content_get(content['sha1'])['data']

    assert resp.status_code == 200
    assert resp['Content-Type'] == 'application/octet-stream'
    assert resp['Content-disposition'] == \
        'attachment; filename=%s_%s' % \
        ('sha1', content['sha1'])
    assert resp.content == content_data

    url = reverse('browse-content-raw',
                  url_args={'query_string': content['sha1']},
                  query_params={'filename': filename})

    resp = client.get(url)

    assert resp.status_code == 200
    assert resp['Content-Type'] == 'application/octet-stream'
    assert resp['Content-disposition'] == \
        'attachment; filename=%s' % filename
    assert resp.content == content_data


@given(invalid_sha1(), unknown_content())
def test_content_request_errors(client, invalid_sha1, unknown_content):
    url = reverse('browse-content',
                  url_args={'query_string': invalid_sha1})
    resp = client.get(url)
    assert resp.status_code == 400
    assert_template_used(resp, 'error.html')

    url = reverse('browse-content',
                  url_args={'query_string': unknown_content['sha1']})
    resp = client.get(url)
    assert resp.status_code == 404
    assert_template_used(resp, 'error.html')


@given(content())
def test_content_bytes_missing(client, archive_data, mocker, content):
    mock_service = mocker.patch('swh.web.browse.utils.service')
    content_data = archive_data.content_get_metadata(content['sha1'])
    content_data['data'] = None

    mock_service.lookup_content.return_value = content_data
    mock_service.lookup_content_filetype.side_effect = Exception()
    mock_service.lookup_content_raw.side_effect = NotFoundExc(
        'Content bytes not available!')

    url = reverse('browse-content',
                  url_args={'query_string': content['sha1']})

    resp = client.get(url)

    assert resp.status_code == 404
    assert_template_used(resp, 'browse/content.html')


def test_content_too_large(client, mocker):
    mock_request_content = mocker.patch(
        'swh.web.browse.views.content.request_content')
    stub_content_too_large_data = {
        'checksums': {
            'sha1': '8624bcdae55baeef00cd11d5dfcfa60f68710a02',
            'sha1_git': '94a9ed024d3859793618152ea559a168bbcbb5e2',
            'sha256': ('8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b16'
                        '5a1dcd80c7c545eb65b903'),
            'blake2s256': ('38702b7168c7785bfe748b51b45d9856070ba90'
                           'f9dc6d90f2ea75d4356411ffe')
        },
        'length': 30000000,
        'raw_data': None,
        'mimetype': 'text/plain',
        'encoding': 'us-ascii',
        'language': 'not detected',
        'licenses': 'GPL',
        'error_code': 200,
        'error_message': '',
        'error_description': ''
    }

    content_sha1 = stub_content_too_large_data['checksums']['sha1']

    mock_request_content.return_value = stub_content_too_large_data

    url = reverse('browse-content',
                  url_args={'query_string': content_sha1})

    url_raw = reverse('browse-content-raw',
                      url_args={'query_string': content_sha1})

    resp = client.get(url)

    assert resp.status_code == 200
    assert_template_used(resp, 'browse/content.html')

    assert_contains(resp, 'Content is too large to be displayed')
    assert_contains(resp, url_raw)


@given(content())
def test_content_uppercase(client, content):
    url = reverse('browse-content-uppercase-checksum',
                  url_args={'query_string': content['sha1'].upper()})
    resp = client.get(url)
    assert resp.status_code == 302

    redirect_url = reverse('browse-content',
                           url_args={'query_string': content['sha1']})

    assert resp['location'] == redirect_url


@given(content_utf8_detected_as_binary())
def test_content_utf8_detected_as_binary_display(client, archive_data,
                                                 content):
    url = reverse('browse-content',
                  url_args={'query_string': content['sha1']})
    resp = client.get(url)

    content_display = _process_content_for_display(archive_data, content)

    assert_contains(resp, escape(content_display['content_data']))


def _process_content_for_display(archive_data, content):
    content_data = archive_data.content_get(content['sha1'])

    mime_type, encoding = get_mimetype_and_encoding_for_content(
        content_data['data'])

    mime_type, encoding, content_data = _re_encode_content(
        mime_type, encoding, content_data['data'])

    content_display = prepare_content_for_display(content_data, mime_type,
                                                  content['path'])

    assert type(content_display['content_data']) == str

    return content_display
