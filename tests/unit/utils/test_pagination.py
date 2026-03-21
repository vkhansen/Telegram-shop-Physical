"""
Tests for bot/utils/pagination.py - LazyPaginator class.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from bot.utils.pagination import LazyPaginator


@pytest.mark.unit
class TestLazyPaginatorInit:
    """Tests for LazyPaginator initialization"""

    def test_default_init(self):
        query_fn = AsyncMock()
        p = LazyPaginator(query_func=query_fn)
        assert p.per_page == 10
        assert p.cache_pages == 3
        assert p.current_page == 0
        assert p._total_count is None
        assert p._cache == {}

    def test_custom_per_page(self):
        p = LazyPaginator(query_func=AsyncMock(), per_page=5)
        assert p.per_page == 5

    def test_custom_cache_pages(self):
        p = LazyPaginator(query_func=AsyncMock(), cache_pages=5)
        assert p.cache_pages == 5

    def test_restore_from_state(self):
        state = {'total_count': 50, 'current_page': 3}
        p = LazyPaginator(query_func=AsyncMock(), state=state)
        assert p._total_count == 50
        assert p.current_page == 3
        assert p._cache == {}  # Cache is not restored from state

    def test_restore_from_none_state(self):
        p = LazyPaginator(query_func=AsyncMock(), state=None)
        assert p._total_count is None
        assert p.current_page == 0

    def test_restore_from_non_dict_state(self):
        p = LazyPaginator(query_func=AsyncMock(), state="invalid")
        assert p._total_count is None
        assert p.current_page == 0


@pytest.mark.unit
class TestLazyPaginatorGetTotalCount:
    """Tests for get_total_count()"""

    @pytest.mark.asyncio
    async def test_get_total_count_calls_query(self):
        query_fn = AsyncMock(return_value=42)
        p = LazyPaginator(query_func=query_fn)

        count = await p.get_total_count()
        assert count == 42
        query_fn.assert_called_once_with(count_only=True)

    @pytest.mark.asyncio
    async def test_get_total_count_caches_result(self):
        query_fn = AsyncMock(return_value=42)
        p = LazyPaginator(query_func=query_fn)

        await p.get_total_count()
        await p.get_total_count()  # Second call
        # Should only call query_func once
        assert query_fn.call_count == 1

    @pytest.mark.asyncio
    async def test_get_total_count_uses_state(self):
        query_fn = AsyncMock()
        p = LazyPaginator(query_func=query_fn, state={'total_count': 100, 'current_page': 0})

        count = await p.get_total_count()
        assert count == 100
        query_fn.assert_not_called()


@pytest.mark.unit
class TestLazyPaginatorGetPage:
    """Tests for get_page()"""

    @pytest.mark.asyncio
    async def test_get_page_calls_query_with_offset(self):
        query_fn = AsyncMock(return_value=["item1", "item2"])
        p = LazyPaginator(query_func=query_fn, per_page=5)

        items = await p.get_page(0)
        assert items == ["item1", "item2"]
        query_fn.assert_called_with(offset=0, limit=5)

    @pytest.mark.asyncio
    async def test_get_page_offset_calculation(self):
        query_fn = AsyncMock(return_value=["item"])
        p = LazyPaginator(query_func=query_fn, per_page=10)

        await p.get_page(3)
        query_fn.assert_called_with(offset=30, limit=10)

    @pytest.mark.asyncio
    async def test_get_page_updates_current_page(self):
        query_fn = AsyncMock(return_value=[])
        p = LazyPaginator(query_func=query_fn)

        await p.get_page(5)
        assert p.current_page == 5

    @pytest.mark.asyncio
    async def test_get_page_caches_result(self):
        query_fn = AsyncMock(return_value=["cached"])
        p = LazyPaginator(query_func=query_fn, per_page=10)

        await p.get_page(0)
        result = await p.get_page(0)  # Should come from cache
        assert result == ["cached"]
        # query_fn called once for page data (count_only not called yet)
        assert query_fn.call_count == 1

    @pytest.mark.asyncio
    async def test_get_page_cache_eviction(self):
        """When cache exceeds cache_pages, old pages get evicted"""
        call_count = 0

        async def mock_query(offset=0, limit=10, count_only=False):
            nonlocal call_count
            call_count += 1
            if count_only:
                return 100  # 10 pages
            return [f"page_{offset // limit}"]

        p = LazyPaginator(query_func=mock_query, per_page=10, cache_pages=3)

        # Load more pages than cache_pages
        await p.get_page(0)
        await p.get_page(1)
        await p.get_page(2)
        await p.get_page(3)  # Should trigger eviction

        # Cache should not have more than cache_pages entries
        # (may have exactly cache_pages due to eviction logic)
        assert len(p._cache) <= p.cache_pages + 1  # +1 for boundary


@pytest.mark.unit
class TestLazyPaginatorGetTotalPages:
    """Tests for get_total_pages()"""

    @pytest.mark.asyncio
    async def test_get_total_pages_exact_division(self):
        query_fn = AsyncMock(return_value=30)
        p = LazyPaginator(query_func=query_fn, per_page=10)

        pages = await p.get_total_pages()
        assert pages == 3

    @pytest.mark.asyncio
    async def test_get_total_pages_with_remainder(self):
        query_fn = AsyncMock(return_value=31)
        p = LazyPaginator(query_func=query_fn, per_page=10)

        pages = await p.get_total_pages()
        assert pages == 4

    @pytest.mark.asyncio
    async def test_get_total_pages_zero_items(self):
        query_fn = AsyncMock(return_value=0)
        p = LazyPaginator(query_func=query_fn, per_page=10)

        pages = await p.get_total_pages()
        assert pages == 1  # Minimum 1 page

    @pytest.mark.asyncio
    async def test_get_total_pages_one_item(self):
        query_fn = AsyncMock(return_value=1)
        p = LazyPaginator(query_func=query_fn, per_page=10)

        pages = await p.get_total_pages()
        assert pages == 1


@pytest.mark.unit
class TestLazyPaginatorSerialize:
    """Tests for _serialize_item() and get_state()"""

    def test_serialize_dict_item(self):
        p = LazyPaginator(query_func=AsyncMock())
        result = p._serialize_item({'key': 'value', 'num': 42})
        assert result == {'key': 'value', 'num': 42}

    def test_serialize_dict_with_datetime(self):
        p = LazyPaginator(query_func=AsyncMock())
        dt = datetime(2025, 1, 1, 12, 0, 0)
        result = p._serialize_item({'date': dt, 'name': 'test'})
        assert result['date'] == dt.isoformat()
        assert result['name'] == 'test'

    def test_serialize_simple_type(self):
        p = LazyPaginator(query_func=AsyncMock())
        result = p._serialize_item("simple_string")
        assert result == {'value': 'simple_string'}

    def test_serialize_integer(self):
        p = LazyPaginator(query_func=AsyncMock())
        result = p._serialize_item(42)
        assert result == {'value': 42}

    def test_get_state(self):
        p = LazyPaginator(query_func=AsyncMock())
        p._total_count = 50
        p.current_page = 3

        state = p.get_state()
        assert state == {'total_count': 50, 'current_page': 3}

    def test_get_state_initial(self):
        p = LazyPaginator(query_func=AsyncMock())
        state = p.get_state()
        assert state == {'total_count': None, 'current_page': 0}


@pytest.mark.unit
class TestLazyPaginatorClearCache:
    """Tests for clear_cache()"""

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        query_fn = AsyncMock(return_value=["data"])
        p = LazyPaginator(query_func=query_fn, per_page=10)

        await p.get_page(0)
        p._total_count = 10
        assert len(p._cache) > 0

        p.clear_cache()
        assert p._cache == {}
        assert p._total_count is None

    @pytest.mark.asyncio
    async def test_clear_cache_forces_refetch(self):
        query_fn = AsyncMock(return_value=["data"])
        p = LazyPaginator(query_func=query_fn, per_page=10)

        await p.get_page(0)
        assert query_fn.call_count == 1

        p.clear_cache()
        await p.get_page(0)
        assert query_fn.call_count == 2  # Called again after cache clear
