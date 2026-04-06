"""Tests for utility functions."""
import pytest
from ticket_management_system.utils import format_pagination_response
from unittest.mock import Mock


class TestFormatPaginationResponse:
    """Test pagination response formatting."""

    def test_format_pagination_response_first_page(self):
        """Test formatting pagination response for first page."""
        # Mock pagination object
        mock_pagination = Mock()
        mock_pagination.page = 1
        mock_pagination.per_page = 10
        mock_pagination.pages = 5
        mock_pagination.total = 50
        mock_pagination.has_next = True
        mock_pagination.has_prev = False
        mock_pagination.next_num = 2
        mock_pagination.prev_num = None

        data = [{'id': '1', 'name': 'Item 1'}, {'id': '2', 'name': 'Item 2'}]
        result = format_pagination_response('items', data, mock_pagination)

        assert result['items'] == data
        assert result['pagination']['page'] == 1
        assert result['pagination']['per_page'] == 10
        assert result['pagination']['total_pages'] == 5
        assert result['pagination']['total_items'] == 50
        assert result['pagination']['has_next'] is True
        assert result['pagination']['has_prev'] is False
        assert result['pagination']['next_page'] == 2
        assert result['pagination']['prev_page'] is None

    def test_format_pagination_response_middle_page(self):
        """Test formatting pagination response for middle page."""
        mock_pagination = Mock()
        mock_pagination.page = 3
        mock_pagination.per_page = 10
        mock_pagination.pages = 5
        mock_pagination.total = 50
        mock_pagination.has_next = True
        mock_pagination.has_prev = True
        mock_pagination.next_num = 4
        mock_pagination.prev_num = 2

        data = [{'id': str(i)} for i in range(10)]
        result = format_pagination_response('items', data, mock_pagination)

        assert result['pagination']['page'] == 3
        assert result['pagination']['has_next'] is True
        assert result['pagination']['has_prev'] is True
        assert result['pagination']['next_page'] == 4
        assert result['pagination']['prev_page'] == 2

    def test_format_pagination_response_last_page(self):
        """Test formatting pagination response for last page."""
        mock_pagination = Mock()
        mock_pagination.page = 5
        mock_pagination.per_page = 10
        mock_pagination.pages = 5
        mock_pagination.total = 50
        mock_pagination.has_next = False
        mock_pagination.has_prev = True
        mock_pagination.next_num = None
        mock_pagination.prev_num = 4

        data = [{'id': str(i)} for i in range(10)]
        result = format_pagination_response('items', data, mock_pagination)

        assert result['pagination']['page'] == 5
        assert result['pagination']['has_next'] is False
        assert result['pagination']['has_prev'] is True
        assert result['pagination']['next_page'] is None
        assert result['pagination']['prev_page'] == 4

    def test_format_pagination_response_empty_data(self):
        """Test formatting pagination response with empty data."""
        mock_pagination = Mock()
        mock_pagination.page = 1
        mock_pagination.per_page = 10
        mock_pagination.pages = 0
        mock_pagination.total = 0
        mock_pagination.has_next = False
        mock_pagination.has_prev = False
        mock_pagination.next_num = None
        mock_pagination.prev_num = None

        data = []
        result = format_pagination_response('items', data, mock_pagination)

        assert result['items'] == []
        assert result['pagination']['total_items'] == 0




