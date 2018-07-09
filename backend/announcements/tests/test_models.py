import pytest
from mixer.backend.django import mixer

# We need to do this so that writing to the DB is possible in our tests.
pytestmark = pytest.mark.django_db


def test_company():
    obj = mixer.blend('announcements.Company')
    assert obj.pk > 0

def test_announcement():
    obj = mixer.blend('announcements.Announcement')
    assert obj.pk > 0
