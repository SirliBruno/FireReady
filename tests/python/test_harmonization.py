import pytest
from pipeline.harmonization import assign_cell, match_candidates, aggregate_units, quality_pass, Config

def obs(ident,sensor,x,y,t,satellite=None,confidence='n',frp=None,partition='training'):
    return {'observation_id':ident,'sensor':sensor,'satellite':satellite or ('Terra' if sensor=='MODIS' else 'Suomi NPP'),'x':x,'y':y,'acquisition_datetime_utc':t,'confidence_raw':confidence,'frp_mw':frp,'partition':partition}

def test_cell_is_deterministic_at_boundary():
    assert assign_cell(1000,2000,1000)=='1000:1:2'
    assert assign_cell(999.9,2000,1000)=='1000:0:2'

def test_candidate_one_to_many_and_temporal_spatial_exclusions():
    rows=[obs('m','MODIS',0,0,'2020-01-01T12:00:00+00:00',confidence='80'),obs('v1','VIIRS',100,0,'2020-01-01T12:30:00+00:00'),obs('v2','VIIRS',200,0,'2020-01-01T12:45:00+00:00'),obs('late','VIIRS',10,0,'2020-01-01T14:00:00+00:00'),obs('far','VIIRS',3000,0,'2020-01-01T12:15:00+00:00')]
    pairs=match_candidates(rows,Config())
    assert {(p['modis_id'],p['viirs_id']) for p in pairs}=={('m','v1'),('m','v2')}
    assert all(p['ambiguous'] for p in pairs)
    units=aggregate_units(rows,pairs,Config())
    assert sum(u['total_source_observations'] for u in units)==5
    assert sum(u['potential_cross_sensor_matches'] for u in units)==2
    assert sum(u['unmatched_viirs_observations'] for u in units)==2

def test_partition_boundaries_never_match():
    rows=[obs('m','MODIS',0,0,'2020-12-31T23:50:00+00:00',confidence='80'),obs('v','VIIRS',0,0,'2021-01-01T00:10:00+00:00',partition='validation')]
    assert not match_candidates(rows,Config())

def test_sensor_quality_rules():
    assert quality_pass(obs('m','MODIS',0,0,'2020-01-01T00:00:00Z',confidence='29'),'all')
    assert not quality_pass(obs('m','MODIS',0,0,'2020-01-01T00:00:00Z',confidence='29'),'conservative')
    assert not quality_pass(obs('v','VIIRS',0,0,'2020-01-01T00:00:00Z',confidence='l'),'conservative')
    assert quality_pass(obs('v','VIIRS',0,0,'2020-01-01T00:00:00Z',confidence='n'),'conservative')

def test_quality_exclusion_and_noaa_reference_cohort():
    from pipeline.harmonization import cohort_pass
    assert not cohort_pass(obs('n','VIIRS',0,0,'2020-01-01T00:00:00Z',satellite='NOAA-20'),'reference')
    assert cohort_pass(obs('n','VIIRS',0,0,'2020-01-01T00:00:00Z',satellite='NOAA-20'),'all')

def test_empty_agreement_has_no_fabricated_ratio():
    from pipeline.harmonization import descriptive
    result=descriptive([],[],Config())
    assert result['positive_grid_day_jaccard'] is None and result['potential_pair_edges']==0

def test_lock_is_write_once_and_checks_partition_hash(tmp_path):
    import json
    from pipeline.harmonization import freeze_reference,load_lock
    source=tmp_path/'source';source.mkdir();out=tmp_path/'out'
    (source/'dataset_manifest.json').write_text(json.dumps({'dataset_id':'a'*64,'classification':'real','file_errors':[]}),encoding='utf8')
    for part in ('training','validation','test'):(source/(part+'_observations.parquet')).write_bytes(part.encode())
    freeze_reference(source,out)
    with pytest.raises(FileExistsError):freeze_reference(source,out)
    (source/'test_observations.parquet').write_bytes(b'changed')
    with pytest.raises(ValueError,match='partition file changed'):load_lock(source,out)

def test_locked_boundary_change_is_rejected(tmp_path):
    import json,hashlib
    from pipeline.harmonization import freeze_reference,load_lock
    source=tmp_path/'source';source.mkdir();out=tmp_path/'out';b=b'original';(source/'maui_boundary.geojson').write_bytes(b)
    (source/'dataset_manifest.json').write_text(json.dumps({'dataset_id':'a'*64,'classification':'real','file_errors':[],'boundary_sha256':hashlib.sha256(b).hexdigest()}),encoding='utf8')
    for part in ('training','validation','test'):(source/(part+'_observations.parquet')).write_bytes(part.encode())
    freeze_reference(source,out);(source/'maui_boundary.geojson').write_bytes(b'changed')
    with pytest.raises(ValueError,match='boundary'):load_lock(source,out)

def test_sensitivity_rejects_any_test_partition():
    from pipeline.harmonization import sensitivity
    with pytest.raises(ValueError,match='held-out'):
        sensitivity([obs('t','VIIRS',0,0,'2023-01-01T00:00:00Z',partition='test')])

def test_full_mock_harmonization_and_heldout_separation(tmp_path):
    import json
    import pandas as pd
    from pipeline.core import ingest
    from pipeline.harmonization import freeze_reference,run_harmonization
    raw=tmp_path/'mock_raw';raw.mkdir()
    (raw/'m.csv').write_text('latitude,longitude,brightness,acq_date,acq_time,satellite,instrument,confidence,version\n20.8,-156.3,320,2020-01-01,1200,T,MODIS,80,6.1\n20.8,-156.3,320,2023-01-01,1200,T,MODIS,80,6.1\n',encoding='utf8')
    (raw/'v.csv').write_text('latitude,longitude,bright_ti4,acq_date,acq_time,satellite,instrument,confidence,version\n20.8,-156.3,310,2020-01-01,1230,N,VIIRS,n,2\n20.8,-156.3,310,2023-01-01,1230,N,VIIRS,n,2\n',encoding='utf8')
    source=tmp_path/'mock_processed';ingest(raw,source,classification='real',boundary_path='data/boundaries/maui-coastline.geojson')
    out=tmp_path/'output';freeze_reference(source,out);report=run_harmonization(source,out)
    assert report['partitions']['training']['potential_pair_edges']==1
    assert report['partitions']['test']['potential_pair_edges']==1
    assert set(pd.read_parquet(out/'artifacts'/'training_activity.parquet').year)=={2020}
    assert set(pd.read_parquet(out/'artifacts'/'test_activity.parquet').year)=={2023}
    sensitivity_data=json.loads((out/'artifacts'/'sensitivity_analysis.json').read_text(encoding='utf8'))
    assert sensitivity_data['scope']=='training and validation only' and len(sensitivity_data['results'])==180
    preview=json.loads((out/'artifacts'/'research_preview.json').read_text(encoding='utf8'))
    assert preview['classification']=='real-unverified' and len(preview['observations']['features'])==4
