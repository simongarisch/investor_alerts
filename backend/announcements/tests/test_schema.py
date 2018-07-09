import pytest
from mixer.backend.django import mixer

from graphql_relay.node.node import to_global_id

import schema

pytestmark = pytest.mark.django_db


def test_company_type():
    instance = schema.CompanyType()
    assert instance


def test_resolve_all_companies():
    mixer.blend('simple_app.Company')
    mixer.blend('simple_app.Company')
    q = schema.Query()
    res = q.resolve_all_companies(None, None)
    assert res.count() == 2, 'Should return all companies'

def test_resolve_company():
    company = mixer.blend('announcements.Company')
    q = schema.Query()
    id = to_global_id('CompanyType', company.pk)
    res = q.resolve_company({'id':id}, None)
    assert res == msg, 'Should return the requested company'
