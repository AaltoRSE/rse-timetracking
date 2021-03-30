from pytest import raises

from rse_timetracking.kpis import parse_KPIs


def test_parse_kpis():
    """Test parsing note bodies containing KPI sections"""
    assert next(parse_KPIs('/Timesaved 2d')) == ('timesaved', 57600)
    assert next(parse_KPIs('/Timesaved 1h 3m 1s')) == ('timesaved', 3781)
    assert next(parse_KPIs('/timesaved: 1s')) == ('timesaved', 1)
    assert next(parse_KPIs('/tiMesaVEd: 1W  ')) == ('timesaved', 144000)
    assert next(parse_KPIs('/timesaved:1m')) == ('timesaved', 60)
    assert next(parse_KPIs('/timesaved1s')) == ('timesaved', 1)
    with raises(RuntimeError, match='Could not parse 1'):
        next(parse_KPIs('time saved: 1'))
    with raises(RuntimeError, match='Could not parse'):
        next(parse_KPIs('time savedsdfjiov2910jbjka.....#(!!@'))

    assert next(parse_KPIs('/projects 5')) == ('projects', 5)
    assert next(parse_KPIs('/projects: 500')) == ('projects', 500)
    assert next(parse_KPIs('/projects:1')) == ('projects', 1)
    assert next(parse_KPIs('/projects4')) == ('projects', 4)
    with raises(ValueError, match='invalid literal for int()'):
        next(parse_KPIs('/projects: foo'))

    assert next(parse_KPIs('/publications 5')) == ('publications', 5)
    assert next(parse_KPIs('/publications: 500')) == ('publications', 500)
    assert next(parse_KPIs('/publications:1')) == ('publications', 1)
    assert next(parse_KPIs('/publications4')) == ('publications', 4)
    with raises(ValueError, match='invalid literal for int()'):
        next(parse_KPIs('/publications: foo'))

    assert next(parse_KPIs('/outputs 5')) == ('outputs', 5)
    assert next(parse_KPIs('/outputs: 500')) == ('outputs', 500)
    assert next(parse_KPIs('/outputs:1')) == ('outputs', 1)
    assert next(parse_KPIs('/outputs4')) == ('outputs', 4)
    with raises(ValueError, match='invalid literal for int()'):
        next(parse_KPIs('/outputs: foo'))

    with raises(StopIteration):
        next(parse_KPIs('foo bar'))
