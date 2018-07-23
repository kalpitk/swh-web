# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from nose.tools import istest
from rest_framework.test import APITestCase
from unittest.mock import patch

from swh.model.identifiers import REVISION

from swh.web.common.utils import reverse
from swh.web.common.exc import NotFoundExc
from swh.web.tests.testbase import SWHWebTestBase


class SwhIdsApiTestCase(SWHWebTestBase, APITestCase):

    @istest
    @patch('swh.web.api.views.identifiers.service')
    def swh_id_resolve_success(self, mock_service):
        rev_id = '96db9023b881d7cd9f379b0c154650d6c108e9a3'
        origin = 'https://github.com/openssl/openssl'
        swh_id = 'swh:1:rev:%s;origin=%s' % (rev_id, origin)
        url = reverse('resolve-swh-pid', kwargs={'swh_id': swh_id})

        mock_service.lookup_revision.return_value = {}

        resp = self.client.get(url)

        browse_rev_url = reverse('browse-revision',
                                 kwargs={'sha1_git': rev_id},
                                 query_params={'origin': origin})

        expected_result = {
            'browse_url': browse_rev_url,
            'metadata': {'origin': origin},
            'namespace': 'swh',
            'object_id': rev_id,
            'object_type': REVISION,
            'scheme_version': 1
        }

        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.data, expected_result)

    @istest
    def swh_id_resolve_invalid(self):
        rev_id_invalid = '96db9023b8_foo_50d6c108e9a3'
        swh_id = 'swh:1:rev:%s' % rev_id_invalid
        url = reverse('resolve-swh-pid', kwargs={'swh_id': swh_id})

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 400)

    @istest
    @patch('swh.web.api.views.identifiers.service')
    def swh_id_resolve_not_found(self, mock_service):
        rev_id_not_found = '56db90232881d7cd9e379b0c154650d6c108e9a1'

        swh_id = 'swh:1:rev:%s' % rev_id_not_found
        url = reverse('resolve-swh-pid', kwargs={'swh_id': swh_id})

        mock_service.lookup_revision.side_effect = NotFoundExc('Revision not found !') # noqa

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 404)