# Copyright (C) 2018-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import math

from django.core.cache import cache

from swh.web.common.exc import NotFoundExc
from swh.web.common.utils import parse_timestamp


def get_origin_visits(origin_info):
    """Function that returns the list of visits for a swh origin.
    That list is put in cache in order to speedup the navigation
    in the swh web browse ui.

    Args:
        origin_info (dict): dict describing the origin to fetch visits from

    Returns:
        list: A list of dict describing the origin visits with the
        following keys:

            * **date**: UTC visit date in ISO format,
            * **origin**: the origin url
            * **status**: the visit status, either **full**, **partial**
              or **ongoing**
            * **visit**: the visit id
            * **type**: the visit type

    Raises:
        swh.web.common.exc.NotFoundExc: if the origin is not found
    """

    from swh.web.common import service

    if 'url' in origin_info:
        origin_url = origin_info['url']
    else:
        origin_url = service.lookup_origin(origin_info)['url']

    cache_entry_id = 'origin_visits_%s' % origin_url
    cache_entry = cache.get(cache_entry_id)

    if cache_entry:
        last_visit = cache_entry[-1]['visit']
        new_visits = list(service.lookup_origin_visits(origin_url,
                                                       last_visit=last_visit))
        if not new_visits:
            last_snp = service.lookup_latest_origin_snapshot(origin_url)
            if not last_snp or last_snp['id'] == cache_entry[-1]['snapshot']:
                return cache_entry

    origin_visits = []

    per_page = service.MAX_LIMIT
    last_visit = None
    while 1:
        visits = list(service.lookup_origin_visits(origin_url,
                                                   last_visit=last_visit,
                                                   per_page=per_page))
        origin_visits += visits
        if len(visits) < per_page:
            break
        else:
            if not last_visit:
                last_visit = per_page
            else:
                last_visit += per_page

    def _visit_sort_key(visit):
        ts = parse_timestamp(visit['date']).timestamp()
        return ts + (float(visit['visit']) / 10e3)

    for v in origin_visits:
        if 'metadata' in v:
            del v['metadata']
    origin_visits = [dict(t) for t in set([tuple(d.items())
                                           for d in origin_visits])]
    origin_visits = sorted(origin_visits, key=lambda v: _visit_sort_key(v))

    cache.set(cache_entry_id, origin_visits)

    return origin_visits


def get_origin_visit(origin_info, visit_ts=None, visit_id=None,
                     snapshot_id=None):
    """Function that returns information about a visit for
    a given origin.
    The visit is retrieved from a provided timestamp.
    The closest visit from that timestamp is selected.

    Args:
        origin_info (dict): a dict filled with origin information
        visit_ts (int or str): an ISO date string or Unix timestamp to parse

    Returns:
        A dict containing the visit info as described below::

            {'origin': 'https://forge.softwareheritage.org/source/swh-web/',
             'date': '2017-10-08T11:54:25.582463+00:00',
             'metadata': {},
             'visit': 25,
             'status': 'full'}

    """
    visits = get_origin_visits(origin_info)

    if not visits:
        raise NotFoundExc(('No visit associated to origin with'
                           ' url %s!' % origin_info['url']))

    if snapshot_id:
        visit = [v for v in visits if v['snapshot'] == snapshot_id]
        if len(visit) == 0:
            raise NotFoundExc(('Visit for snapshot with id %s for origin with'
                               ' url %s not found!' %
                               (snapshot_id, origin_info['url'])))
        return visit[0]

    if visit_id:
        visit = [v for v in visits if v['visit'] == int(visit_id)]
        if len(visit) == 0:
            raise NotFoundExc(('Visit with id %s for origin with'
                               ' url %s not found!' %
                               (visit_id, origin_info['url'])))
        return visit[0]

    if not visit_ts:
        # returns the latest full visit when no timestamp is provided
        for v in reversed(visits):
            if v['status'] == 'full':
                return v
        return visits[-1]

    target_visit_ts = math.floor(parse_timestamp(visit_ts).timestamp())

    # Find the visit with date closest to the target (in absolute value)
    (abs_time_delta, visit_idx) = min(
        ((math.floor(parse_timestamp(visit['date']).timestamp()), i)
         for (i, visit) in enumerate(visits)),
        key=lambda ts_and_i: abs(ts_and_i[0] - target_visit_ts))

    if visit_idx is not None:
        visit = visits[visit_idx]
        # If multiple visits have the same date, select the one with
        # the largest id.
        while visit_idx < len(visits) - 1 and \
                visit['date'] == visits[visit_idx+1]['date']:
            visit_idx = visit_idx + 1
            visit = visits[visit_idx]
        return visit
    else:
        raise NotFoundExc(('Visit with timestamp %s for origin with '
                           'url %s not found!' %
                           (visit_ts, origin_info['url'])))
