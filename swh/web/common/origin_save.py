# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from swh.web import config
from swh.web.common.exc import BadInputExc, ForbiddenExc
from swh.web.common.models import (
    SaveUnauthorizedOrigin, SaveAuthorizedOrigin, SaveOriginRequest,
    SAVE_REQUEST_ACCEPTED, SAVE_REQUEST_REJECTED, SAVE_REQUEST_PENDING
)

from swh.scheduler.utils import create_oneshot_task_dict

scheduler = config.scheduler()


def get_origin_save_authorized_urls():
    """
    Get the list of origin url prefixes authorized to be
    immediately loaded into the archive (whitelist).

    Returns:
        list: The list of authorized origin url prefix
    """
    return [origin.url
            for origin in SaveAuthorizedOrigin.objects.all()]


def get_origin_save_unauthorized_urls():
    """
    Get the list of origin url prefixes forbidden to be
    loaded into the archive (blacklist).

    Returns:
        list: the list of unauthorized origin url prefix
    """
    return [origin.url
            for origin in SaveUnauthorizedOrigin.objects.all()]


def can_save_origin(origin_url):
    """
    Check if a software origin can be saved into the archive.

    Based on the origin url, the save request will be either:

      * immediately accepted if the url is whitelisted
      * rejected if the url is blacklisted
      * put in pending state for manual review otherwise

    Args:
        origin_url (str): the software origin url to check

    Returns:
        str: the origin save request status, either *accepted*,
        *rejected* or *pending*
    """
    # origin url may be blacklisted
    for url_prefix in get_origin_save_unauthorized_urls():
        if origin_url.startswith(url_prefix):
            return SAVE_REQUEST_REJECTED

    # if the origin url is in the white list, it can be immediately saved
    for url_prefix in get_origin_save_authorized_urls():
        if origin_url.startswith(url_prefix):
            return SAVE_REQUEST_ACCEPTED

    # otherwise, the origin url needs to be manually verified
    return SAVE_REQUEST_PENDING


# map origin type to scheduler task
# TODO: do not hardcode the task name here
# TODO: unlock hg and svn loading once the scheduler
#       loading tasks are available in production
_origin_type_task = {
    'git': 'origin-update-git',
    # 'hg': 'origin-load-hg',
    # 'svn': 'origin-load-svn'
}

SAVE_TASK_NOT_CREATED = 'not created'
SAVE_TASK_NOT_YET_SCHEDULED = 'not yet scheduled'
SAVE_TASK_SCHEDULED = 'scheduled'
SAVE_TASK_SUCCEED = 'succeed'
SAVE_TASK_FAILED = 'failed'

# map scheduler task status to origin save status
_save_task_status = {
    'next_run_not_scheduled': SAVE_TASK_NOT_YET_SCHEDULED,
    'next_run_scheduled': SAVE_TASK_SCHEDULED,
    'completed': SAVE_TASK_SUCCEED,
    'disabled': SAVE_TASK_FAILED
}


def get_savable_origin_types():
    return sorted(list(_origin_type_task.keys()))


def _check_origin_type_savable(origin_type):
    """
    Get the list of software origin types that can be loaded
    through a save request.

    Returns:
        list: the list of savable origin types
    """
    allowed_origin_types = ', '.join(get_savable_origin_types())
    if origin_type not in _origin_type_task:
        raise BadInputExc('Origin of type %s can not be saved! '
                          'Allowed types are the following: %s' %
                          (origin_type, allowed_origin_types))


_validate_url = URLValidator(schemes=['http', 'https', 'svn'])


def _check_origin_url_valid(origin_url):
    try:
        _validate_url(origin_url)
    except ValidationError:
        raise BadInputExc('The provided origin url (%s) is not valid!' %
                          origin_url)


def _save_request_dict(save_request, task=None):
    save_task_status = SAVE_TASK_NOT_CREATED
    if task:
        save_task_status = _save_task_status[task['status']]
    return {'origin_type': save_request.origin_type,
            'origin_url': save_request.origin_url,
            'save_request_date': save_request.request_date.isoformat(),
            'save_request_status': save_request.status,
            'save_task_status': save_task_status}


def create_save_origin_request(origin_type, origin_url):
    """
    Create a loading task to save a software origin into the archive.

    This function aims to create a software origin loading task
    trough the use of the swh-scheduler component.

    First, some checks are performed to see if the origin type and
    url are valid but also if the the save request can be accepted.
    If those checks passed, the loading task is then created.
    Otherwise, the save request is put in pending or rejected state.

    All the submitted save requests are logged into the swh-web
    database to keep track of them.

    Args:
        origin_type (str): the type of origin to save (*git*, *hg*, *svn*, ...)
        origin_url (str): the url of the origin to save

    Raises:
        BadInputExc: the origin type or url is invalid
        ForbiddenExc: the provided origin url is blacklisted

    Returns:
        dict: A dict describing the save request with the following keys:

            * **origin_type**: the type of the origin to save
            * **origin_url**: the url of the origin
            * **save_request_date**: the date the request was submitted
            * **save_request_status**: the request status, either *accepted*,
              *rejected* or *pending*
            * **save_task_status**: the origin loading task status, either
              *not created*, *not yet scheduled*, *scheduled*, *succeed* or
              *failed*


    """
    _check_origin_type_savable(origin_type)
    _check_origin_url_valid(origin_url)
    save_request_status = can_save_origin(origin_url)
    task = None

    # if the origin save request is accepted, create a scheduler
    # task to load it into the archive
    if save_request_status == SAVE_REQUEST_ACCEPTED:
        # create a task with high priority
        kwargs = {'priority': 'high'}
        # set task parameters according to the origin type
        if origin_type == 'git':
            kwargs['repo_url'] = origin_url
        elif origin_type == 'hg':
            kwargs['origin_url'] = origin_url
        elif origin_type == 'svn':
            kwargs['origin_url'] = origin_url
            kwargs['svn_url'] = origin_url

        sor = None
        # get list of previously sumitted save requests
        current_sors = \
            list(SaveOriginRequest.objects.filter(origin_type=origin_type,
                                                  origin_url=origin_url))

        can_create_task = False
        # if no save requests previously submitted, create the scheduler task
        if not current_sors:
            can_create_task = True
        else:
            # get the latest submitted save request
            sor = current_sors[0]
            # if it was in pending state, we need to create the scheduler task
            # and update the save request info in the database
            if sor.status == SAVE_REQUEST_PENDING:
                can_create_task = True
            # a task has already been created to load the origin
            elif sor.loading_task_id != -1:
                # get the scheduler task and its status
                task = scheduler.get_tasks([sor.loading_task_id])[0]
                save_task_status = _save_task_status[task['status']]
                # create a new scheduler task only if the previous one has been
                # already executed
                if save_task_status == SAVE_TASK_FAILED or \
                   save_task_status == SAVE_TASK_SUCCEED:
                    can_create_task = True
                    sor = None
                else:
                    can_create_task = False

        if can_create_task:
            # effectively create the scheduler task
            task_dict = create_oneshot_task_dict(
                _origin_type_task[origin_type], **kwargs)
            task = scheduler.create_tasks([task_dict])[0]

            # pending save request has been accepted
            if sor:
                sor.status = SAVE_REQUEST_ACCEPTED
                sor.loading_task_id = task['id']
                sor.save()
            else:
                sor = SaveOriginRequest.objects.create(origin_type=origin_type,
                                                       origin_url=origin_url,
                                                       status=save_request_status, # noqa
                                                       loading_task_id=task['id']) # noqa
    # save request must be manually reviewed for acceptation
    elif save_request_status == SAVE_REQUEST_PENDING:
        # check if there is already such a save request already submitted,
        # no need to add it to the database in that case
        try:
            sor = SaveOriginRequest.objects.get(origin_type=origin_type,
                                                origin_url=origin_url,
                                                status=save_request_status)
        # if not add it to the database
        except ObjectDoesNotExist:
            sor = SaveOriginRequest.objects.create(origin_type=origin_type,
                                                   origin_url=origin_url,
                                                   status=save_request_status)
    # origin can not be saved as its url is blacklisted,
    # log the request to the database anyway
    else:
        sor = SaveOriginRequest.objects.create(origin_type=origin_type,
                                               origin_url=origin_url,
                                               status=save_request_status)

    if save_request_status == SAVE_REQUEST_REJECTED:
        raise ForbiddenExc('The origin url is blacklisted and will not be '
                           'loaded into the archive.')

    return _save_request_dict(sor, task)


def get_save_origin_requests_from_queryset(requests_queryset):
    """
    Get all save requests from a SaveOriginRequest queryset.

    Args:
        requests_queryset (django.db.models.QuerySet): input
            SaveOriginRequest queryset

    Returns:
        list: A list of save origin requests dict as described in
        :func:`swh.web.common.origin_save.create_save_origin_request`
    """
    requests = []
    for sor in requests_queryset:
        # rejected saving task or pending for acceptation
        if sor.loading_task_id == -1:
            requests.append(_save_request_dict(sor))
            continue
        task = scheduler.get_tasks([sor.loading_task_id])
        # loading task may have been archived, do not return
        # save request info in that case
        if task:
            requests.append(_save_request_dict(sor, task[0]))
    return requests


def get_save_origin_requests(origin_type, origin_url):
    """
    Get all save requests for a given software origin.

    Args:
        origin_type (str): the type of the origin
        origin_url (str): the url of the origin

    Raises:
        BadInputExc: the origin type or url is invalid

    Returns:
        list: A list of save origin requests dict as described in
        :func:`swh.web.common.origin_save.create_save_origin_request`
    """
    _check_origin_type_savable(origin_type)
    _check_origin_url_valid(origin_url)
    sors = SaveOriginRequest.objects.filter(origin_type=origin_type,
                                            origin_url=origin_url)
    return get_save_origin_requests_from_queryset(sors)