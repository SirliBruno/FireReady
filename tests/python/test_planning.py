def test_planning_artifact_integrity():
    import json
    from pathlib import Path
    data=json.loads(Path('public/data/planning/maui.json').read_text(encoding='utf-8'))
    assert len(data['grid'])==len({c['id'] for c in data['grid']})
    assert all(c['area_m2']>0 for c in data['grid'])
    assert len(data['costs_km'])==len(data['stations'])
    assert all(len(row)==len(data['grid']) and min(row)>=0 for row in data['costs_km'])
    assert set(data['monthly_weights'])=={str(i) for i in range(1,13)}
    assert abs(sum(sum(v) for v in data['monthly_weights'].values())*8-397)<1e-9

def test_historical_evaluation_has_bounded_metrics():
    import json
    from pathlib import Path
    d=json.loads(Path('public/data/planning/historical_validation.json').read_text(encoding='utf-8'))
    assert len(d['results'])==12
    for row in d['results']:
        assert row['actual_mean_area_fraction']<=row['requested_area_fraction']+1e-10
        assert 0<=row['captured_positive_cell_days']<=row['positive_cell_days']
        assert 0<=row['capture_fraction']<=1
        assert row['positive_cell_days']=={'validation':52,'test':131}[row['partition']]

def test_train_only_monthly_demands_and_grid_alignment():
    import json
    from pathlib import Path
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from collections import Counter
    planning=json.loads(Path('public/data/planning/maui.json').read_text(encoding='utf-8'))
    reference=json.loads(Path('public/data/research/harmonization.json').read_text(encoding='utf-8'))
    ids={c['id'] for c in planning['grid']}
    assert all(f['properties']['gridId'] in ids for f in reference['observations']['features'])
    days={(p['gridId'],datetime.fromisoformat(p['acquiredAt']).astimezone(ZoneInfo('Pacific/Honolulu')).date().isoformat()) for f in reference['observations']['features'] if (p:=f['properties'])['partition']=='training'}
    counts=Counter((cell,int(date[5:7])) for cell,date in days)
    for month in range(1,13):
        assert planning['monthly_weights'][str(month)]==[counts[(cell['id'],month)]/8 for cell in planning['grid']]
