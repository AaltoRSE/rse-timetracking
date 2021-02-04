from pytest import raises

from rse_timetracking.kpis import parse_KPIs


def test_parse_kpis():
    """Test parsing note bodies containing KPI sections"""
    assert parse_KPIs('Time saved 2d') == ('Researcher time saved', 57600)
    assert parse_KPIs('Time saved 1h 3m 1s') == ('Researcher time saved', 3781)
    assert parse_KPIs('time saved: 1s') == ('Researcher time saved', 1)
    assert parse_KPIs('tiMe saVEd: 1W  ') == ('Researcher time saved', 144000)
    assert parse_KPIs('time saved:1m') == ('Researcher time saved', 60)
    assert parse_KPIs('time saved1s') == ('Researcher time saved', 1)
    with raises(RuntimeError, match='Could not parse 1'):
        parse_KPIs('time saved: 1')
    with raises(RuntimeError, match='Could not parse'):
        parse_KPIs('time savedsdfjiov2910jbjka.....#(!!@')

    assert parse_KPIs('ongoing projects 5') == ('Projects supported', 5)
    assert parse_KPIs('ongoing projects: 500') == ('Projects supported', 500)
    assert parse_KPIs('ongoing projects:1') == ('Projects supported', 1)
    assert parse_KPIs('ongoing projects4') == ('Projects supported', 4)
    with raises(ValueError, match='invalid literal for int()'):
        parse_KPIs('ongoing projects: foo')

    assert parse_KPIs('publications 5') == ('Publications supported', 5)
    assert parse_KPIs('publications: 500') == ('Publications supported', 500)
    assert parse_KPIs('publications:1') == ('Publications supported', 1)
    assert parse_KPIs('publications4') == ('Publications supported', 4)
    with raises(ValueError, match='invalid literal for int()'):
        parse_KPIs('publications: foo')

    assert parse_KPIs('open outputs 5') == ('Open outputs', 5)
    assert parse_KPIs('open outputs: 500') == ('Open outputs', 500)
    assert parse_KPIs('open outputs:1') == ('Open outputs', 1)
    assert parse_KPIs('open outputs4') == ('Open outputs', 4)
    with raises(ValueError, match='invalid literal for int()'):
        parse_KPIs('open outputs: foo')

    assert parse_KPIs('foo bar') is None
