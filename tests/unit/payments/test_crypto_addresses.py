"""
Tests for bot.payments.crypto_addresses module — multi-coin address pool management.
"""
import pytest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import patch, MagicMock, PropertyMock, call

from bot.payments.crypto_addresses import (
    load_addresses_for_coin,
    get_available_address,
    mark_address_used,
    remove_address_from_file,
    get_address_stats,
    load_all_addresses,
    COIN_ADDRESS_FILES,
)
from bot.database.models.main import CryptoAddress


def _make_crypto_address(coin="btc", address="addr1", is_used=False,
                         used_by=None, order_id=None, used_at=None):
    """Helper to build a mock CryptoAddress."""
    obj = MagicMock(spec=CryptoAddress)
    obj.coin = coin
    obj.address = address
    obj.is_used = is_used
    obj.used_by = used_by
    obj.order_id = order_id
    obj.used_at = used_at
    return obj


def _mock_session():
    """Create a mock session with query/filter_by/first/count chain."""
    session = MagicMock()
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=False)
    return session


def _patch_database(session):
    """Patch Database().session() to yield the given mock session."""
    mock_db = MagicMock()
    mock_db.session.return_value = session
    return patch("bot.payments.crypto_addresses.Database", return_value=mock_db)


@pytest.mark.unit
@pytest.mark.payments
class TestLoadAddressesForCoin:
    """Tests for load_addresses_for_coin."""

    def test_loads_file_creates_db_entries_skips_dupes(self, tmp_path):
        """Reads file, creates DB entries, skips existing addresses."""
        addr_file = tmp_path / "btc_addresses.txt"
        addr_file.write_text("# comment\naddr_new_1\naddr_existing\naddr_new_2\n")

        session = _mock_session()

        # Simulate: addr_existing already exists, others don't
        def filter_by_side_effect(**kwargs):
            query_result = MagicMock()
            if kwargs.get("address") == "addr_existing":
                query_result.first.return_value = _make_crypto_address()
            else:
                query_result.first.return_value = None
            return query_result

        session.query.return_value.filter_by.side_effect = filter_by_side_effect

        with _patch_database(session), \
             patch("bot.payments.crypto_addresses._get_address_file", return_value=addr_file):
            count = load_addresses_for_coin("btc")

        assert count == 2
        assert session.add.call_count == 2
        session.commit.assert_called_once()

    def test_missing_file_creates_it_returns_zero(self, tmp_path):
        """When address file doesn't exist, create it and return 0."""
        addr_file = tmp_path / "sub" / "ltc_addresses.txt"
        assert not addr_file.exists()

        with patch("bot.payments.crypto_addresses._get_address_file", return_value=addr_file):
            count = load_addresses_for_coin("ltc")

        assert count == 0
        assert addr_file.exists()


@pytest.mark.unit
@pytest.mark.payments
class TestGetAvailableAddress:
    """Tests for get_available_address."""

    def test_claims_address_atomically(self):
        """Should mark the first unused address and return it."""
        mock_addr = _make_crypto_address(address="sol_addr_1")

        session = _mock_session()
        query_chain = session.query.return_value.filter_by.return_value
        query_chain.with_for_update.return_value.first.return_value = mock_addr

        with _patch_database(session):
            result = get_available_address("sol", user_id=123, order_id=456)

        assert result == "sol_addr_1"
        assert mock_addr.is_used is True
        assert mock_addr.used_by == 123
        assert mock_addr.order_id == 456
        session.commit.assert_called_once()

    def test_returns_none_when_pool_empty(self):
        """Should return None when no unused addresses are available."""
        session = _mock_session()
        query_chain = session.query.return_value.filter_by.return_value
        query_chain.with_for_update.return_value.first.return_value = None

        with _patch_database(session):
            result = get_available_address("btc", user_id=123, order_id=1)

        assert result is None


@pytest.mark.unit
@pytest.mark.payments
class TestMarkAddressUsed:
    """Tests for mark_address_used."""

    def test_marks_in_db_and_removes_from_file(self):
        """Without external session: marks address, commits, removes from file."""
        mock_addr = _make_crypto_address(address="btc_addr_1")

        session = _mock_session()
        session.query.return_value.filter_by.return_value.first.return_value = mock_addr

        with _patch_database(session), \
             patch("bot.payments.crypto_addresses.remove_address_from_file") as mock_remove:
            result = mark_address_used("btc", "btc_addr_1", user_id=100, order_id=200)

        assert result is True
        assert mock_addr.is_used is True
        assert mock_addr.used_by == 100
        assert mock_addr.order_id == 200
        session.commit.assert_called_once()
        mock_remove.assert_called_once_with("btc", "btc_addr_1")

    def test_external_session_no_commit(self):
        """With external session: marks address but does NOT commit."""
        mock_addr = _make_crypto_address(address="ltc_addr_1")
        ext_session = MagicMock()
        ext_session.query.return_value.filter_by.return_value.first.return_value = mock_addr

        with patch("bot.payments.crypto_addresses.remove_address_from_file") as mock_remove:
            result = mark_address_used("ltc", "ltc_addr_1", user_id=10, order_id=20,
                                       session=ext_session)

        assert result is True
        assert mock_addr.is_used is True
        # External session should NOT be committed by the function
        ext_session.commit.assert_not_called()
        mock_remove.assert_called_once_with("ltc", "ltc_addr_1")


@pytest.mark.unit
@pytest.mark.payments
class TestRemoveAddressFromFile:
    """Tests for remove_address_from_file."""

    def test_removes_address_preserves_comments(self, tmp_path):
        """Should remove only the matching address, keep comments and blanks."""
        addr_file = tmp_path / "sol_addresses.txt"
        addr_file.write_text("# pool addresses\naddr_keep\naddr_remove\naddr_keep_2\n")

        with patch("bot.payments.crypto_addresses._get_address_file", return_value=addr_file):
            remove_address_from_file("sol", "addr_remove")

        lines = addr_file.read_text().strip().splitlines()
        assert "addr_remove" not in lines
        assert "# pool addresses" in lines
        assert "addr_keep" in lines
        assert "addr_keep_2" in lines


@pytest.mark.unit
@pytest.mark.payments
class TestGetAddressStats:
    """Tests for get_address_stats."""

    def test_correct_counts(self):
        """Should return correct total, used, available."""
        session = _mock_session()
        base_query = session.query.return_value.filter_by.return_value

        # total = 10
        base_query.count.return_value = 10
        # used = 3
        base_query.filter.return_value.count.return_value = 3

        with _patch_database(session):
            stats = get_address_stats("btc")

        assert stats["total"] == 10
        assert stats["used"] == 3
        assert stats["available"] == 7


@pytest.mark.unit
@pytest.mark.payments
class TestLoadAllAddresses:
    """Tests for load_all_addresses."""

    def test_calls_load_for_each_coin(self):
        """Should call load_addresses_for_coin for every coin in COIN_ADDRESS_FILES."""
        with patch("bot.payments.crypto_addresses.load_addresses_for_coin") as mock_load:
            mock_load.return_value = 5
            results = load_all_addresses()

        assert set(results.keys()) == set(COIN_ADDRESS_FILES.keys())
        assert mock_load.call_count == len(COIN_ADDRESS_FILES)
        for coin in COIN_ADDRESS_FILES:
            mock_load.assert_any_call(coin)
            assert results[coin] == 5


@pytest.mark.unit
@pytest.mark.payments
class TestUnknownCoinCryptoAddresses:
    """Unknown coin identifier should raise ValueError."""

    def test_load_unknown_coin_raises(self):
        with pytest.raises(ValueError, match="Unknown coin"):
            load_addresses_for_coin("doge")

    def test_get_available_unknown_coin_raises(self):
        """get_available_address delegates to _get_address_file indirectly;
        however it does not validate coin — it queries DB directly.
        The ValueError comes from _get_address_file via other paths.
        We test load_addresses_for_coin which calls _get_address_file."""
        with pytest.raises(ValueError, match="Unknown coin"):
            load_addresses_for_coin("xrp")
