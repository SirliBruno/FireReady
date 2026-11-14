from pipeline.seasonal import aggregate_local_days

def obs(id,at,cell='c',partition='training',sensor='MODIS'):
    return {'properties':{'id':id,'acquiredAt':at,'gridId':cell,'partition':partition,'sensor':sensor}}

def test_local_day_deduplicates_and_handles_leap_day():
    rows=[obs('a','2020-03-01T04:00:00+00:00'),obs('b','2020-02-29T23:30:00+00:00',sensor='VIIRS'),obs('c','2020-03-01T11:00:00+00:00')]
    result=aggregate_local_days(rows)
    assert len(result)==2
    feb=next(x for x in result if x['local_date']=='2020-02-29')
    assert feb['observation_count']==2
    assert set(feb['sensors'])=={'MODIS','VIIRS'}
    assert feb['source_observation_ids']==['a','b']

def test_split_is_preserved_at_new_year_and_empty_data():
    rows=[obs('a','2021-01-01T02:00:00+00:00',partition='validation')]
    result=aggregate_local_days(rows)
    assert result[0]['local_date']=='2020-12-31'
    assert result[0]['partition']=='validation'
    assert aggregate_local_days([])==[]

def test_actual_reference_reconciles_when_local_artifacts_available():
    import json
    from pathlib import Path
    import pytest
    p=Path('data/processed/harmonization/real/artifacts/research_preview.json')
    if not p.exists(): pytest.skip('local research artifact unavailable')
    data=json.loads(p.read_text(encoding='utf-8'))
    rows=aggregate_local_days(data['observations']['features'])
    assert sum(r['observation_count'] for r in rows)==data['report']['selected_reference_count']
    assert len({identifier for row in rows for identifier in row['source_observation_ids']})==len(data['observations']['features'])
    assert {r['grid_cell_id'] for r in rows} <= {f['properties']['grid_cell_id'] for f in data['grid']['features']}
