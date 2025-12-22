"""Unit tests for the Timestamp class."""
from datetime import datetime, timezone

import pytest

from hiero_sdk_python.timestamp import Timestamp

pytestmark = pytest.mark.unit


def test_constructor():
    """Test basic Timestamp construction."""
    timestamp = Timestamp(seconds=1234567890, nanos=123456789)
    assert timestamp.seconds == 1234567890
    assert timestamp.nanos == 123456789


def test_generate_with_jitter():
    """Test Timestamp generation with jitter enabled."""
    timestamp = Timestamp.generate(has_jitter=True)
    assert timestamp.seconds > 0
    assert 0 <= timestamp.nanos < Timestamp.MAX_NS


def test_generate_without_jitter():
    """Test Timestamp generation without jitter."""
    timestamp = Timestamp.generate(has_jitter=False)
    assert timestamp.seconds > 0
    assert 0 <= timestamp.nanos < Timestamp.MAX_NS


def test_from_date_datetime():
    """Test creating Timestamp from datetime object."""
    dt = datetime(2024, 1, 15, 12, 30, 45, 123456, tzinfo=timezone.utc)
    timestamp = Timestamp.from_date(dt)

    assert timestamp.seconds == int(dt.timestamp())
    # Check nanos is within expected range (may have minor rounding differences)
    assert 123456000 <= timestamp.nanos <= 123456999


def test_from_date_int():
    """Test creating Timestamp from integer (seconds since epoch)."""
    seconds = 1234567890
    timestamp = Timestamp.from_date(seconds)

    assert timestamp.seconds == seconds
    assert timestamp.nanos == 0


def test_from_date_string():
    """Test creating Timestamp from ISO 8601 string."""
    date_string = "2024-01-15T12:30:45.123456"
    timestamp = Timestamp.from_date(date_string)

    assert timestamp.seconds > 0
    assert timestamp.nanos >= 0


def test_from_date_invalid_type():
    """Test that invalid type raises ValueError."""
    with pytest.raises(ValueError, match="Invalid type for 'date'"):
        Timestamp.from_date([1, 2, 3])


def test_to_date():
    """Test converting Timestamp to datetime."""
    timestamp = Timestamp(seconds=1705324245, nanos=123456000)
    dt = timestamp.to_date()

    assert isinstance(dt, datetime)
    assert dt.tzinfo == timezone.utc
    assert dt.timestamp() == pytest.approx(1705324245.123456, rel=1e-6)


def test_plus_nanos():
    """Test adding nanoseconds to Timestamp."""
    timestamp = Timestamp(seconds=100, nanos=500_000_000)

    # Add nanoseconds without overflow
    new_timestamp = timestamp.plus_nanos(200_000_000)
    assert new_timestamp.seconds == 100
    assert new_timestamp.nanos == 700_000_000

    # Add nanoseconds with overflow to next second
    new_timestamp2 = timestamp.plus_nanos(600_000_000)
    assert new_timestamp2.seconds == 101
    assert new_timestamp2.nanos == 100_000_000

    # Add nanoseconds with multiple seconds overflow
    new_timestamp3 = timestamp.plus_nanos(2_500_000_000)
    assert new_timestamp3.seconds == 103
    assert new_timestamp3.nanos == 0


def test_str():
    """Test string representation."""
    timestamp = Timestamp(seconds=1234567890, nanos=123456789)
    assert str(timestamp) == "1234567890.123456789"

    # Test with leading zeros in nanos
    timestamp2 = Timestamp(seconds=100, nanos=1234)
    assert str(timestamp2) == "100.000001234"


def test_repr():
    """Test repr representation for debugging."""
    timestamp = Timestamp(seconds=1234567890, nanos=123456789)
    repr_str = repr(timestamp)

    assert repr_str == "Timestamp(seconds=1234567890, nanos=123456789)"
    # Verify it's evaluable (contains the constructor format)
    assert "Timestamp(" in repr_str
    assert "seconds=" in repr_str
    assert "nanos=" in repr_str


def test_compare():
    """Test comparing two Timestamps."""
    ts1 = Timestamp(seconds=100, nanos=500_000_000)
    ts2 = Timestamp(seconds=100, nanos=600_000_000)
    ts3 = Timestamp(seconds=101, nanos=400_000_000)
    ts4 = Timestamp(seconds=100, nanos=500_000_000)

    # Earlier seconds
    assert ts1.compare(ts3) == -1

    # Later seconds
    assert ts3.compare(ts1) == 1

    # Same seconds, earlier nanos
    assert ts1.compare(ts2) == -1

    # Same seconds, later nanos
    assert ts2.compare(ts1) == 1

    # Equal timestamps
    assert ts1.compare(ts4) == 0


def test_equality():
    """Test equality comparison."""
    ts1 = Timestamp(seconds=100, nanos=500_000_000)
    ts2 = Timestamp(seconds=100, nanos=500_000_000)
    ts3 = Timestamp(seconds=100, nanos=600_000_000)
    ts4 = Timestamp(seconds=101, nanos=500_000_000)

    # Equal timestamps
    assert ts1 == ts2

    # Different nanos
    assert ts1 != ts3

    # Different seconds
    assert ts1 != ts4

    # Not equal to different type
    assert ts1 != "timestamp"
    assert ts1 != 100


def test_hash():
    """Test hashing for use in sets and dicts."""
    ts1 = Timestamp(seconds=100, nanos=500_000_000)
    ts2 = Timestamp(seconds=100, nanos=500_000_000)
    ts3 = Timestamp(seconds=100, nanos=600_000_000)

    # Equal timestamps should have same hash
    assert hash(ts1) == hash(ts2)

    # Different timestamps should (usually) have different hashes
    assert hash(ts1) != hash(ts3)

    # Can be used in sets
    timestamp_set = {ts1, ts2, ts3}
    assert len(timestamp_set) == 2  # ts1 and ts2 are equal

    # Can be used as dict keys
    timestamp_dict = {ts1: "first", ts3: "third"}
    assert len(timestamp_dict) == 2


def test_protobuf_conversion():
    """Test conversion to and from protobuf."""
    original = Timestamp(seconds=1234567890, nanos=123456789)

    # Convert to protobuf
    pb_obj = original._to_protobuf()
    assert pb_obj.seconds == 1234567890
    assert pb_obj.nanos == 123456789

    # Convert back from protobuf
    restored = Timestamp._from_protobuf(pb_obj)
    assert restored.seconds == original.seconds
    assert restored.nanos == original.nanos
    assert restored == original
