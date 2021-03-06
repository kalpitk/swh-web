# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.shortcuts import render, redirect

from swh.web.common import service
from swh.web.common.origin_visits import get_origin_visits
from swh.web.common.utils import (
    reverse, format_utc_iso_date, parse_timestamp
)
from swh.web.common.exc import handle_view_exception
from swh.web.browse.utils import get_snapshot_context
from swh.web.browse.browseurls import browse_route

from .utils.snapshot_context import (
    browse_snapshot_directory, browse_snapshot_content,
    browse_snapshot_log, browse_snapshot_branches,
    browse_snapshot_releases
)


@browse_route(r'origin/(?P<origin_url>.+)/visit/(?P<timestamp>.+)/directory/',
              r'origin/(?P<origin_url>.+)/visit/(?P<timestamp>.+)'
              '/directory/(?P<path>.+)/',
              r'origin/(?P<origin_url>.+)/directory/',
              r'origin/(?P<origin_url>.+)/directory/(?P<path>.+)/',
              view_name='browse-origin-directory')
def origin_directory_browse(request, origin_url,
                            timestamp=None, path=None):
    """Django view for browsing the content of a directory associated
    to an origin for a given visit.

    The url scheme that points to it is the following:

        * :http:get:`/browse/origin/(origin_url)/directory/[(path)/]`
        * :http:get:`/browse/origin/(origin_url)/visit/(timestamp)/directory/[(path)/]`
    """ # noqa
    return browse_snapshot_directory(request, origin_url=origin_url,
                                     timestamp=timestamp, path=path)


@browse_route(r'origin/(?P<origin_url>.+)/visit/(?P<timestamp>.+)'
              '/content/(?P<path>.+)/',
              r'origin/(?P<origin_url>.+)/content/(?P<path>.+)/',
              view_name='browse-origin-content')
def origin_content_browse(request, origin_url, path=None,
                          timestamp=None):
    """Django view that produces an HTML display of a content
    associated to an origin for a given visit.

    The url scheme that points to it is the following:

        * :http:get:`/browse/origin/(origin_url)/content/(path)/`
        * :http:get:`/browse/origin/(origin_url)/visit/(timestamp)/content/(path)/`

    """ # noqa
    language = request.GET.get('language', None)
    return browse_snapshot_content(request,
                                   origin_url=origin_url, timestamp=timestamp,
                                   path=path, selected_language=language)


PER_PAGE = 20


@browse_route(r'origin/(?P<origin_url>.+)/visit/(?P<timestamp>.+)/log/',
              r'origin/(?P<origin_url>.+)/log/',
              view_name='browse-origin-log')
def origin_log_browse(request, origin_url, timestamp=None):
    """Django view that produces an HTML display of revisions history (aka
    the commit log) associated to a software origin.

    The url scheme that points to it is the following:

        * :http:get:`/browse/origin/(origin_url)/log/`
        * :http:get:`/browse/origin/(origin_url)/visit/(timestamp)/log/`
    """ # noqa
    return browse_snapshot_log(request,
                               origin_url=origin_url, timestamp=timestamp)


@browse_route(r'origin/(?P<origin_url>.+)/visit/(?P<timestamp>.+)/branches/',
              r'origin/(?P<origin_url>.+)/branches/',
              view_name='browse-origin-branches')
def origin_branches_browse(request, origin_url, timestamp=None):
    """Django view that produces an HTML display of the list of branches
    associated to an origin for a given visit.

    The url scheme that points to it is the following:

        * :http:get:`/browse/origin/(origin_url)/branches/`
        * :http:get:`/browse/origin/(origin_url)/visit/(timestamp)/branches/`

    """ # noqa
    return browse_snapshot_branches(request,
                                    origin_url=origin_url, timestamp=timestamp)


@browse_route(r'origin/(?P<origin_url>.+)/visit/(?P<timestamp>.+)/releases/',
              r'origin/(?P<origin_url>.+)/releases/',
              view_name='browse-origin-releases')
def origin_releases_browse(request, origin_url, timestamp=None):
    """Django view that produces an HTML display of the list of releases
    associated to an origin for a given visit.

    The url scheme that points to it is the following:

        * :http:get:`/browse/origin/(origin_url)/releases/`
        * :http:get:`/browse/origin/(origin_url)/visit/(timestamp)/releases/`

    """ # noqa
    return browse_snapshot_releases(request,
                                    origin_url=origin_url, timestamp=timestamp)


@browse_route(r'origin/(?P<origin_url>.+)/visits/',
              view_name='browse-origin-visits')
def origin_visits_browse(request, origin_url):
    """Django view that produces an HTML display of visits reporting
    for a given origin.

    The url that points to it is
    :http:get:`/browse/origin/(origin_url)/visits/`.
    """
    try:
        origin_info = service.lookup_origin({'url': origin_url})
        origin_visits = get_origin_visits(origin_info)
        snapshot_context = get_snapshot_context(origin_url=origin_url)
    except Exception as exc:
        return handle_view_exception(request, exc)

    for i, visit in enumerate(origin_visits):
        url_date = format_utc_iso_date(visit['date'], '%Y-%m-%dT%H:%M:%SZ')
        visit['fmt_date'] = format_utc_iso_date(visit['date'])
        query_params = {}
        if i < len(origin_visits) - 1:
            if visit['date'] == origin_visits[i+1]['date']:
                query_params = {'visit_id': visit['visit']}
        if i > 0:
            if visit['date'] == origin_visits[i-1]['date']:
                query_params = {'visit_id': visit['visit']}

        snapshot = visit['snapshot'] if visit['snapshot'] else ''

        visit['browse_url'] = reverse('browse-origin-directory',
                                      url_args={'origin_url': origin_url,
                                                'timestamp': url_date},
                                      query_params=query_params)
        if not snapshot:
            visit['snapshot'] = ''
        visit['date'] = parse_timestamp(visit['date']).timestamp()

    heading = 'Origin visits - %s' % origin_url

    return render(request, 'browse/origin-visits.html',
                  {'heading': heading,
                   'swh_object_name': 'Visits',
                   'swh_object_metadata': origin_info,
                   'origin_visits': origin_visits,
                   'origin_info': origin_info,
                   'snapshot_context': snapshot_context,
                   'vault_cooking': None,
                   'show_actions_menu': False})


@browse_route(r'origin/(?P<origin_url>.+)/',
              view_name='browse-origin')
def origin_browse(request, origin_url):
    """Django view that redirects to the display of the latest archived
    snapshot for a given software origin.
    """
    last_snapshot_url = reverse('browse-origin-directory',
                                url_args={'origin_url': origin_url})
    return redirect(last_snapshot_url)
