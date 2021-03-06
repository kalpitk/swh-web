# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.shortcuts import render
import sentry_sdk

from swh.web.common import service
from swh.web.common.utils import (
    reverse, format_utc_iso_date
)
from swh.web.common.exc import NotFoundExc, handle_view_exception
from swh.web.browse.browseurls import browse_route
from swh.web.browse.utils import (
    gen_revision_link, get_snapshot_context, gen_link,
    gen_snapshot_link, get_swh_persistent_ids, gen_directory_link,
    gen_content_link, gen_release_link, gen_person_mail_link
)


@browse_route(r'release/(?P<sha1_git>[0-9a-f]+)/',
              view_name='browse-release',
              checksum_args=['sha1_git'])
def release_browse(request, sha1_git):
    """
    Django view that produces an HTML display of a release
    identified by its id.

    The url that points to it is :http:get:`/browse/release/(sha1_git)/`.
    """
    try:
        release = service.lookup_release(sha1_git)
        snapshot_context = None
        origin_info = None
        snapshot_id = request.GET.get('snapshot_id', None)
        origin_url = request.GET.get('origin_url', None)
        if not origin_url:
            origin_url = request.GET.get('origin', None)
        timestamp = request.GET.get('timestamp', None)
        visit_id = request.GET.get('visit_id', None)
        if origin_url:
            try:
                snapshot_context = get_snapshot_context(
                    snapshot_id, origin_url, timestamp, visit_id)
            except NotFoundExc:
                raw_rel_url = reverse('browse-release',
                                      url_args={'sha1_git': sha1_git})
                error_message = \
                    ('The Software Heritage archive has a release '
                     'with the hash you provided but the origin '
                     'mentioned in your request appears broken: %s. '
                     'Please check the URL and try again.\n\n'
                     'Nevertheless, you can still browse the release '
                     'without origin information: %s'
                        % (gen_link(origin_url), gen_link(raw_rel_url)))

                raise NotFoundExc(error_message)
            origin_info = snapshot_context['origin_info']
        elif snapshot_id:
            snapshot_context = get_snapshot_context(snapshot_id)
    except Exception as exc:
        return handle_view_exception(request, exc)

    release_data = {}

    release_data['author'] = 'None'
    if release['author']:
        release_data['author'] = gen_person_mail_link(release['author'])
    release_data['date'] = format_utc_iso_date(release['date'])
    release_data['release'] = sha1_git
    release_data['name'] = release['name']
    release_data['synthetic'] = release['synthetic']
    release_data['target'] = release['target']
    release_data['target type'] = release['target_type']

    if snapshot_context:
        if release['target_type'] == 'revision':
            release_data['context-independent target'] = \
                gen_revision_link(release['target'])
        elif release['target_type'] == 'content':
            release_data['context-independent target'] = \
                gen_content_link(release['target'])
        elif release['target_type'] == 'directory':
            release_data['context-independent target'] = \
                gen_directory_link(release['target'])
        elif release['target_type'] == 'release':
            release_data['context-independent target'] = \
                gen_release_link(release['target'])

    release_note_lines = []
    if release['message']:
        release_note_lines = release['message'].split('\n')

    vault_cooking = None

    target_link = None
    if release['target_type'] == 'revision':
        target_link = gen_revision_link(release['target'],
                                        snapshot_context=snapshot_context,
                                        link_text=None, link_attrs=None)
        try:
            revision = service.lookup_revision(release['target'])
            vault_cooking = {
                'directory_context': True,
                'directory_id': revision['directory'],
                'revision_context': True,
                'revision_id': release['target']
            }
        except Exception as exc:
            sentry_sdk.capture_exception(exc)
    elif release['target_type'] == 'directory':
        target_link = gen_directory_link(release['target'],
                                         snapshot_context=snapshot_context,
                                         link_text=None, link_attrs=None)
        try:
            revision = service.lookup_directory(release['target'])
            vault_cooking = {
                'directory_context': True,
                'directory_id': revision['directory'],
                'revision_context': False,
                'revision_id': None
            }
        except Exception as exc:
            sentry_sdk.capture_exception(exc)
    elif release['target_type'] == 'content':
        target_link = gen_content_link(release['target'],
                                       snapshot_context=snapshot_context,
                                       link_text=None, link_attrs=None)
    elif release['target_type'] == 'release':
        target_link = gen_release_link(release['target'],
                                       snapshot_context=snapshot_context,
                                       link_text=None, link_attrs=None)

    release['target_link'] = target_link

    if snapshot_context:
        release_data['snapshot'] = snapshot_context['snapshot_id']

    if origin_info:
        release_data['context-independent release'] = \
            gen_release_link(release['id'])
        release_data['origin url'] = gen_link(origin_info['url'],
                                              origin_info['url'])
        browse_snapshot_link = \
            gen_snapshot_link(snapshot_context['snapshot_id'])
        release_data['context-independent snapshot'] = browse_snapshot_link

    swh_objects = [{'type': 'release',
                    'id': sha1_git}]

    if snapshot_context:
        snapshot_id = snapshot_context['snapshot_id']

    if snapshot_id:
        swh_objects.append({'type': 'snapshot',
                            'id': snapshot_id})

    swh_ids = get_swh_persistent_ids(swh_objects, snapshot_context)

    note_header = 'None'
    if len(release_note_lines) > 0:
        note_header = release_note_lines[0]

    release['note_header'] = note_header
    release['note_body'] = '\n'.join(release_note_lines[1:])

    heading = 'Release - %s' % release['name']
    if snapshot_context:
        context_found = 'snapshot: %s' % snapshot_context['snapshot_id']
        if origin_info:
            context_found = 'origin: %s' % origin_info['url']
        heading += ' - %s' % context_found

    return render(request, 'browse/release.html',
                  {'heading': heading,
                   'swh_object_id': swh_ids[0]['swh_id'],
                   'swh_object_name': 'Release',
                   'swh_object_metadata': release_data,
                   'release': release,
                   'snapshot_context': snapshot_context,
                   'show_actions_menu': True,
                   'breadcrumbs': None,
                   'vault_cooking': vault_cooking,
                   'top_right_link': None,
                   'swh_ids': swh_ids})
