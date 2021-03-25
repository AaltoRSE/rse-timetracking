from pytest import raises

from rse_timetracking.time import parse_time_spent, time_to_seconds


def test_parse_time_spent():
    """Test parsing a Gitlab time tracking message body."""
    body = 'added 1s of time spent at 2021-02-04'
    assert parse_time_spent(body) == ('1s', 'added', '2021-02-04')

    body = 'subtracted 1s of time spent at 2021-02-04'
    assert parse_time_spent(body) == ('1s', 'subtracted', '2021-02-04')

    body = 'added 1w 2d 3h 1s of time spent at 2021-02-04'
    assert parse_time_spent(body) == ('1w 2d 3h 1s', 'added', '2021-02-04')

    # Missing pieces
    body = '2d of time spent'
    assert parse_time_spent(body) is None


def test_time_to_seconds():
    """Test parsing a time string to an integer number of seconds."""
    assert time_to_seconds('1s') == 1
    assert time_to_seconds('5mo 3w 20h 34s') == 3384034

    with raises(RuntimeError, match="Could not parse"):
        time_to_seconds('foo bar')  # Extra spaces not allowed

    with raises(RuntimeError, match="Could not parse"):
        time_to_seconds('1s ')  # Extra spaces not allowed
