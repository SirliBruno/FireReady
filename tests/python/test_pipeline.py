import csv
import json
import zipfile
from pathlib import Path
import pytest
from pipeline.core import parse_utc, partition, ingest, UnsafeArchive, read_sources

@pytest.mark.parametrize('raw,expected', [('0000','00:00'),('35','00:35'),('0950','09:50'),('1230','12:30'),('2359','23:59')])
def test_time(raw, expected):
    assert parse_utc('2020-01-01', raw).strftime('%H:%M') == expected

@pytest.mark.parametrize('raw', ['2460','2360','-1','12345','12.5'])
def test_invalid_time(raw):
    with pytest.raises(ValueError): parse_utc('2020-01-01',raw)

def test_split_boundaries():
    assert partition(parse_utc('2020-12-31','2359')) == 'training'
    assert partition(parse_utc('2021-01-01','0000')) == 'validation'
    assert partition(parse_utc('2022-12-31','2359')) == 'validation'
    assert partition(parse_utc('2023-01-01','0000')) == 'test'

def test_zip_traversal_rejected(tmp_path):
    file=tmp_path/'bad.zip'
    with zipfile.ZipFile(file,'w') as z: z.writestr('../evil.csv','a,b\n1,2')
    with pytest.raises(UnsafeArchive): list(read_sources(file))

def test_end_to_end(tmp_path):
    raw=tmp_path/'raw'; raw.mkdir()
    header=['latitude','longitude','bright_ti4','scan','track','acq_date','acq_time','satellite','instrument','confidence','version','bright_ti5','frp','daynight']
    valid=['20.8','-156.3','320','0.4','0.5','2020-01-01','35','N','VIIRS','n','2.0','290','5','N']
    rows=[valid,valid,['100','-156.3','320','0.4','0.5','2020-01-01','35','N','VIIRS','n','2.0','290','5','N'],['20.8','-156.3','320','0.4','0.5','2023-01-01','0000','N','VIIRS','n','2.0','290','5','N']]
    with (raw/'input.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(header);writer.writerows(rows)
    report=ingest(raw,tmp_path/'out',classification='synthetic')
    assert report['counts']=={'received':4,'accepted':2,'rejected':1,'geographic_excluded':0,'temporal_excluded':0,'duplicates':1}
    assert report['partitions']=={'training':1,'validation':0,'test':1}
    import pandas as pd
    train=pd.read_parquet(tmp_path/'out'/'training_observations.parquet')
    assert list(train.acquisition_year)==[2020]
    assert json.loads((tmp_path/'out'/'dataset_manifest.json').read_text(encoding='utf-8'))['classification']=='synthetic'
from pipeline.publish import publish

def test_synthetic_cannot_publish_as_real(tmp_path):
    source=tmp_path/'source';source.mkdir();(source/'dataset_manifest.json').write_text(json.dumps({'classification':'synthetic'}),encoding='utf-8')
    with pytest.raises(ValueError,match='synthetic'):
        publish(source,tmp_path/'public',reviewer='analyst',evidence='https://example.org/review',source_url='https://example.org/data')
    assert not (tmp_path/'public'/'status.json').exists()

def test_local_timezone_previous_day():
    from zoneinfo import ZoneInfo
    local=parse_utc('2023-01-01','0035').astimezone(ZoneInfo('Pacific/Honolulu'))
    assert local.isoformat()=='2022-12-31T14:35:00-10:00'

def test_sensor_identity_and_optional_fields():
    from pipeline.core import normalize
    row={'latitude':'20.8','longitude':'-156.3','acq_date':'2021-01-01','acq_time':'0000','satellite':'N','instrument':'VIIRS','confidence':'n','bright_ti4':'320'}
    result=normalize(row,'VIIRS','source',2,'synthetic','2026-01-01T00:00:00+00:00')
    assert result['frp_mw'] is None and result['confidence_native_category']=='nominal'
    assert 'frp' in result['quality_flags'] and result['brightness_modis_k'] is None
    with pytest.raises(ValueError): normalize({**row,'confidence':'72'},'VIIRS','source',2,'synthetic','x')
    with pytest.raises(ValueError): normalize({**row,'instrument':'MODIS'},'VIIRS','source',2,'synthetic','x')

def test_provisional_bbox_includes_edges_and_ocean(tmp_path):
    raw=tmp_path/'raw';raw.mkdir(); (raw/'one.csv').write_text('latitude,longitude,brightness,acq_date,acq_time,satellite,confidence\n20.55,-156.75,320,2020-01-01,0000,T,70\n',encoding='utf-8')
    report=ingest(raw,tmp_path/'out',classification='synthetic')
    assert report['counts']['accepted']==1
    assert 'Provisional bounding box' in report['limitations'][0]

def test_empty_directory_and_idempotency(tmp_path):
    raw=tmp_path/'raw';raw.mkdir();out=tmp_path/'out'
    first=ingest(raw,out,classification='synthetic');second=ingest(raw,out,classification='synthetic')
    assert first['counts']==second['counts'] and first['counts']['received']==0
    import pandas as pd
    assert pd.read_parquet(out/'training_observations.parquet').empty

def test_unsafe_archive_rejects_entire_archive(tmp_path):
    raw=tmp_path/'raw';raw.mkdir()
    with zipfile.ZipFile(raw/'bad.zip','w') as z:
        z.writestr('safe.csv','latitude,longitude,brightness,acq_date,acq_time,satellite\n20.8,-156.3,320,2020-01-01,0000,T\n')
        z.writestr('../evil.csv','bad')
    report=ingest(raw,tmp_path/'out',classification='synthetic')
    assert report['counts']['received']==0
    assert 'unsafe archive path' in report['file_errors'][0]['reason']

def test_unsupported_schema_is_reported(tmp_path):
    raw=tmp_path/'raw';raw.mkdir();(raw/'bad.csv').write_text('foo,bar\n1,2\n',encoding='utf-8')
    report=ingest(raw,tmp_path/'out',classification='synthetic')
    assert report['file_errors'] and report['counts']['received']==0

def test_duplicate_across_files_preserves_lineage_and_stable_id(tmp_path):
    raw=tmp_path/'raw';raw.mkdir();content='latitude,longitude,brightness,acq_date,acq_time,satellite,confidence,version\n20.8,-156.3,320,2020-02-01,0035,T,70,6.1\n'
    (raw/'a.csv').write_text(content,encoding='utf8');(raw/'b.csv').write_text(content,encoding='utf8');out=tmp_path/'out'
    result=ingest(raw,out,classification='synthetic');assert result['counts']['duplicates']==1
    import pandas as pd
    first=pd.read_parquet(out/'normalized_observations.parquet').observation_id.tolist()
    lineage=json.loads((out/'duplicate_lineage.json').read_text(encoding='utf8'));assert len(lineage)==1 and lineage[0]['observation_id']==first[0]
    ingest(raw,out,classification='synthetic');assert pd.read_parquet(out/'normalized_observations.parquet').observation_id.tolist()==first

def test_valid_zip_and_modis_confidence(tmp_path):
    raw=tmp_path/'raw';raw.mkdir()
    with zipfile.ZipFile(raw/'data.zip','w') as z:z.writestr('nested/modis.csv','latitude,longitude,brightness,acq_date,acq_time,satellite,confidence,version\n20.8,-156.3,320,2020-01-01,0000,T,70,6.1\n')
    report=ingest(raw,tmp_path/'out',classification='synthetic');assert report['counts']['accepted']==1
    manifest=json.loads((tmp_path/'out'/'dataset_manifest.json').read_text(encoding='utf8'))
    assert manifest['sources'][0]['archive_member']=='nested/modis.csv'

def test_invalid_confidence_and_missing_sensor():
    from pipeline.core import identify,normalize
    with pytest.raises(ValueError):identify(['latitude','longitude','acq_date','acq_time','satellite'])
    row={'latitude':'20.8','longitude':'-156.3','acq_date':'2020-01-01','acq_time':'0000','satellite':'T','confidence':'101'}
    with pytest.raises(ValueError):normalize(row,'MODIS','x',2,'synthetic','x')

def test_invalid_real_manifest_does_not_publish(tmp_path):
    source=tmp_path/'source';source.mkdir();(source/'dataset_manifest.json').write_text(json.dumps({'classification':'real','counts':{'accepted':1},'file_errors':[]}),encoding='utf8')
    with pytest.raises(ValueError):publish(source,tmp_path/'public',reviewer='Tester',evidence='https://example.org/review',source_url='https://example.org/data')
    assert not (tmp_path/'public'/'status.json').exists()

def test_publish_rejects_tampered_spatial_output(tmp_path):
    raw=tmp_path/'mock_raw';raw.mkdir();(raw/'test.csv').write_text('latitude,longitude,brightness,acq_date,acq_time,satellite,confidence,version\n20.8,-156.3,320,2020-01-01,0000,T,70,6.1\n',encoding='utf-8')
    source=tmp_path/'mock_processed';ingest(raw,source,classification='real')
    path=source/'frontend_observations.geojson';geo=json.loads(path.read_text(encoding='utf-8'));geo['features'][0]['geometry']['coordinates'][0]=-150;path.write_text(json.dumps(geo),encoding='utf-8')
    with pytest.raises(ValueError,match='spatial'):
        publish(source,tmp_path/'public',reviewer='test',evidence='https://example.org/review',source_url='https://example.org/source',raw_root=raw)
    assert not (tmp_path/'public'/'status.json').exists()

def test_reviewed_mock_publish_path(tmp_path):
    # All inputs are invented and confined to pytest's temporary directory.
    raw=tmp_path/'mock_raw';raw.mkdir();(raw/'mock.csv').write_text('latitude,longitude,bright_ti4,acq_date,acq_time,satellite,confidence,version\n20.8,-156.3,310,2020-01-01,0035,N,n,2.0\n',encoding='utf8')
    source=tmp_path/'mock_processed';ingest(raw,source,classification='real')
    output=tmp_path/'mock_public';publish(source,output,reviewer='test only',evidence='https://example.org/review',source_url='https://example.org/source',raw_root=raw)
    bundle=json.loads((output/'dataset.json').read_text(encoding='utf8'));geo=json.loads((output/'observations.geojson').read_text(encoding='utf8'))
    assert json.loads((output/'status.json').read_text(encoding='utf8'))['available'] is True
    assert bundle['observations']==[{'year':2019,'month':12,'count':1}]
    assert geo['features'][0]['properties']['sensor']=='VIIRS'
    assert 'raw_record_json' not in json.dumps(geo)

def test_dataset_id_includes_geographic_configuration(tmp_path):
    raw=tmp_path/'raw';raw.mkdir();(raw/'one.csv').write_text('latitude,longitude,brightness,acq_date,acq_time,satellite\n20.8,-156.3,320,2020-01-01,0000,T\n',encoding='utf8')
    out=tmp_path/'out';ingest(raw,out,classification='synthetic');first=json.loads((out/'dataset_manifest.json').read_text(encoding='utf8'))['dataset_id']
    ingest(raw,out,classification='synthetic',bbox=(-157,20,-155,22));second=json.loads((out/'dataset_manifest.json').read_text(encoding='utf8'))['dataset_id']
    assert first!=second

def test_verified_coastline_filters_ocean_and_covers_edge(tmp_path):
    boundary=Path('data/boundaries/maui-coastline.geojson')
    assert boundary.exists()
    raw=tmp_path/'raw';raw.mkdir();ring=json.loads(boundary.read_text(encoding='utf8'))['features'][0]['geometry']['coordinates'][0];edge=ring[0]
    (raw/'m.csv').write_text('latitude,longitude,brightness,acq_date,acq_time,satellite\n20.8,-156.3,320,2020-01-01,0000,T\n20.55,-156.75,320,2020-01-01,0000,T\n'+str(edge[1])+','+str(edge[0])+',320,2020-01-01,0000,T\n',encoding='utf8')
    out=tmp_path/'out';report=ingest(raw,out,classification='synthetic',boundary_path=boundary)
    assert report['counts']['accepted']==2
    assert report['counts']['geographic_excluded']==1
    assert report['geographic_filter']=='maui_coastline_covers'

def test_boundary_tampering_is_rejected(tmp_path):
    source=Path('data/boundaries/maui-coastline.geojson');data=json.loads(source.read_text(encoding='utf8'));data['features'][0]['properties']['sqmi']=999
    boundary=tmp_path/'tampered.geojson';boundary.write_text(json.dumps(data),encoding='utf8');raw=tmp_path/'raw';raw.mkdir()
    with pytest.raises(ValueError,match='boundary hash'):
        ingest(raw,tmp_path/'out',classification='synthetic',boundary_path=boundary)

def test_publish_rejects_mixed_processing_types(tmp_path):
    raw=tmp_path/'mock_raw';raw.mkdir();(raw/'mock.csv').write_text('latitude,longitude,brightness,acq_date,acq_time,satellite,confidence,version\n20.8,-156.3,320,2020-01-01,0000,T,70,6.1\n20.8,-156.3,321,2020-01-02,0000,T,70,6.1NRT\n',encoding='utf8')
    source=tmp_path/'mock_processed';ingest(raw,source,classification='real')
    with pytest.raises(ValueError,match='mixed processing'):
        publish(source,tmp_path/'public',reviewer='test',evidence='https://example.org/review',source_url='https://example.org/source',raw_root=raw)

def test_source_row_number_tracks_physical_csv_lines(tmp_path):
    raw=tmp_path/'raw';raw.mkdir();(raw/'multiline.csv').write_text('latitude,longitude,brightness,acq_date,acq_time,satellite,notes\n20.8,-156.3,320,2020-01-01,0000,T,"line 1\nline 2"\n20.8,-156.3,321,2020-01-02,0000,T,normal\n',encoding='utf8')
    out=tmp_path/'out';ingest(raw,out,classification='synthetic')
    import pandas as pd
    assert pd.read_parquet(out/'normalized_observations.parquet').source_row_number.tolist()==[2,4]

def test_archive_shared_headers_with_satellite_metadata():
    from pipeline.core import identify,normalize
    columns=['latitude','longitude','acq_date','acq_time','satellite','instrument','brightness','bright_t31']
    row={'latitude':'20.8','longitude':'-156.3','acq_date':'2020-01-01','acq_time':'0035','satellite':'SNPP','instrument':'SNPP','brightness':'310','bright_t31':'290','confidence':'n','version':'2'}
    assert identify(columns,[row])=='VIIRS'
    obs=normalize(row,'VIIRS','source',2,'real','2026-01-01T00:00:00Z')
    assert obs['satellite']=='Suomi NPP' and obs['brightness_viirs_i4_k']==310
    assert obs['brightness_viirs_i5_k'] is None
    modis={**row,'satellite':'Terra','instrument':'MODIS','confidence':'70','version':'6.03'}
    assert identify(columns,[modis])=='MODIS'
    assert normalize(modis,'MODIS','s',2,'real','2026-01-01T00:00:00Z')['satellite']=='Terra'

def test_noaa20_archive_processing_not_assumed_standard():
    from pipeline.core import normalize
    row={'latitude':'20.8','longitude':'-156.3','acq_date':'2020-01-01','acq_time':'0035','satellite':'N20','instrument':'VIIRS','bright_ti4':'310','confidence':'n','version':'2'}
    assert normalize(row,'VIIRS','source',2,'real','2026-01-01T00:00:00Z')['processing_type']=='unknown'
