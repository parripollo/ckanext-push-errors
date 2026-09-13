import pytest
from unittest.mock import patch
from ckan.lib import kvstore
from ckanext.push_errors.logging import can_send_message, push_message


@pytest.mark.usefixtures("clean_db")
class TestLimits:
    """The counters live in ckan.lib.kvstore"""

    @pytest.fixture(autouse=True)
    def clean_counters(self):
        kvstore.clear("push_errors:*")

    @pytest.mark.ckan_config("ckanext.push_errors.max_messages_minute", "2")
    def test_minute_limit(self):
        assert can_send_message() is True
        assert can_send_message() is True
        assert can_send_message() is False

    @pytest.mark.ckan_config("ckanext.push_errors.max_messages_minute", "5")
    @pytest.mark.ckan_config("ckanext.push_errors.max_messages_hour", "1")
    def test_hour_limit(self):
        assert can_send_message() is True
        assert can_send_message() is False

    def test_counters_expire(self):
        can_send_message()
        keys = kvstore.keys("push_errors:*")
        assert len(keys) == 2
        for key in keys:
            # expire() only touches existing rows, so True means the
            # counter is there and has a ttl
            assert kvstore.expire(key, 1) is True

    @pytest.mark.ckan_config("ckanext.push_errors.url", "http://mock-url.com")
    @pytest.mark.ckan_config("ckanext.push_errors.max_messages_minute", "1")
    @patch("ckanext.push_errors.logging.requests.post")
    def test_second_message_is_not_sent(self, mock_post):
        mock_post.return_value.status_code = 200
        push_message("first")
        push_message("second")
        assert mock_post.call_count == 1
