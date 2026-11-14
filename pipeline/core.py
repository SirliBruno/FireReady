"""FIRMS ingestion. This module performs no cross-sensor harmonization."""
from __future__ import annotations
import csv, hashlib, io, json, math, os, re, shutil, tempfile, zipfile
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath
from zoneinfo import ZoneInfo

BBOX=(-156.75,20.55,-155.95,21.10)
OFFICIAL_BOUNDARY_SHA256='5f918822bb2e523924c9bc917afe81af3491efa43c80388b7bbf3ce4d1b35d7c'
START=date(2013,1,1); END=date(2023,12,31)
SATELLITES={'MODIS':{'T':'Terra','TERRA':'Terra','A':'Aqua','AQUA':'Aqua'},'VIIRS':{'N':'Suomi NPP','SNPP':'Suomi NPP','S-NPP':'Suomi NPP','1':'NOAA-20','N20':'NOAA-20','2':'NOAA-21','N21':'NOAA-21'}}
AVAILABILITY={'NOAA-20':date(2018,4,1),'NOAA-21':date(2024,1,17),'Suomi NPP':date(2012,1,20)}
class UnsafeArchive(ValueError): pass

def parse_utc(day, time):
    time=str(time).strip()
    if not re.fullmatch(r'\d{1,4}',time): raise ValueError('invalid acquisition time')
    hhmm=time.zfill(4); hour=int(hhmm[:2]); minute=int(hhmm[2:])
    if hour>23 or minute>59: raise ValueError('invalid acquisition time')
    d=date.fromisoformat(str(day).strip())
    return datetime(d.year,d.month,d.day,hour,minute,tzinfo=timezone.utc)

def partition(dt):
    y=dt.astimezone(timezone.utc).year
    if 2013<=y<=2020: return 'training'
    if 2021<=y<=2022: return 'validation'
    if y==2023: return 'test'
    raise ValueError('outside study period')

def sha(data): return hashlib.sha256(data).hexdigest()

def read_sources(path):
    """Read CSV bytes directly from safe ZIP entries; never extract to disk."""
    path=Path(path)
    if path.suffix.lower()=='.csv':
        yield path.name,path.read_bytes();return
    if path.suffix.lower()!='.zip': return
    with zipfile.ZipFile(path) as z:
        entries=z.infolist()
        if len(entries)>10000 or sum(e.file_size for e in entries)>500_000_000: raise UnsafeArchive('archive exceeds safety limit')
        for entry in entries:
            name=entry.filename; p=PurePosixPath(name)
            if '\\' in name or p.is_absolute() or '..' in p.parts or re.match(r'^[A-Za-z]:',name): raise UnsafeArchive('unsafe archive path')
            if entry.flag_bits & 1: raise UnsafeArchive('encrypted archive')
        for entry in entries:
            if not entry.is_dir() and entry.filename.lower().endswith('.csv'):
                yield entry.filename,z.read(entry)

def identify(headers,rows=None):
    h=set(headers)
    if not {'latitude','longitude','acq_date','acq_time','satellite'}<=h: raise ValueError('missing required columns')
    instruments={(str(r.get('instrument') or '').strip().upper()) for r in (rows or []) if str(r.get('instrument') or '').strip()}
    mapped={'VIIRS' if x in ('VIIRS','SNPP','S-NPP') else 'MODIS' if x=='MODIS' else 'unknown' for x in instruments}
    if 'unknown' in mapped or len(mapped)>1:raise ValueError('unsupported or mixed instrument metadata')
    viirs=bool({'bright_ti4','bright_ti5'}&h); modis=bool({'brightness','bright_t31'}&h)
    if mapped:
        sensor=next(iter(mapped))
        if sensor=='MODIS' and viirs:raise ValueError('instrument conflicts with schema')
        return sensor
    if viirs==modis: raise ValueError('unsupported or ambiguous sensor schema')
    return 'VIIRS' if viirs else 'MODIS'

def number(value,name,positive=False,nonnegative=False):
    if value is None or str(value).strip()=='': return None
    try: n=float(value)
    except (ValueError,TypeError): raise ValueError('invalid '+name)
    if not math.isfinite(n) or (positive and n<=0) or (nonnegative and n<0): raise ValueError('invalid '+name)
    return n

def processing(version):
    if not version:return 'unknown'
    v=version.strip().upper()
    for suffix in ('URT','NRT','RT'):
        if re.fullmatch(r'\d+(?:\.\d+)*'+suffix,v):return suffix
    if re.fullmatch(r'\d+(?:\.\d+)*',v):return 'standard'
    return 'unknown'

def normalize(row,sensor,source_id,row_number,classification,stamp):
    lat=number(row.get('latitude'),'latitude');lon=number(row.get('longitude'),'longitude')
    if lat is None or lon is None or not -90<=lat<=90 or not -180<=lon<=180: raise ValueError('invalid coordinates')
    dt=parse_utc(row.get('acq_date',''),row.get('acq_time',''))
    sat=SATELLITES[sensor].get(str(row.get('satellite','')).strip().upper())
    if not sat:raise ValueError('unrecognized satellite')
    if sat in AVAILABILITY and dt.date()<AVAILABILITY[sat]:raise ValueError('before product availability')
    instrument=(row.get('instrument') or '').strip().upper()
    if instrument and instrument not in (('VIIRS','SNPP','S-NPP') if sensor=='VIIRS' else ('MODIS',)):raise ValueError('instrument conflicts with schema')
    raw=(row.get('confidence') or '').strip(); native=None
    if raw:
        if sensor=='MODIS':
            conf=number(raw,'confidence')
            if not 0<=conf<=100:raise ValueError('invalid MODIS confidence')
        else:
            native={'l':'low','n':'nominal','h':'high'}.get(raw.lower())
            if not native:raise ValueError('invalid VIIRS confidence')
    dn=(row.get('daynight') or '').strip().upper()
    if dn and dn not in ('D','N'):raise ValueError('invalid daynight')
    frp=number(row.get('frp'),'frp',nonnegative=True);scan=number(row.get('scan'),'scan',positive=True);track=number(row.get('track'),'track',positive=True)
    mb=number(row.get('brightness'),'brightness',positive=True) if sensor=='MODIS' else None
    i4=number(row.get('bright_ti4') or row.get('brightness'),'bright_ti4',positive=True) if sensor=='VIIRS' else None
    i5=number(row.get('bright_ti5'),'bright_ti5',positive=True) if sensor=='VIIRS' else None
    fire_type=(row.get('type') or '').strip() or None
    if fire_type is not None and fire_type not in ('0','1','2','3'):raise ValueError('invalid fire type')
    version=(row.get('version') or '').strip() or None
    local=dt.astimezone(ZoneInfo('Pacific/Honolulu'))
    missing=[k for k,v in {'frp':frp,'scan':scan,'track':track,'confidence':raw or None,'version':version}.items() if v is None]
    raw_json=json.dumps(row,sort_keys=True,ensure_ascii=False,separators=(',',':'))
    # Exact raw attributes + sensor, not proximity: differing sensors or values remain separate.
    observation_id=sha((sensor+'\n'+raw_json).encode('utf-8'))
    return {'observation_id':observation_id,'source_file_id':source_id,'source_row_number':row_number,'source_product':sensor+' active fire','sensor':sensor,'satellite':sat,'latitude':lat,'longitude':lon,'acquisition_datetime_utc':dt.isoformat(),'acquisition_date_utc':dt.date().isoformat(),'local_datetime':local.isoformat(),'local_date':local.date().isoformat(),'acquisition_year':dt.year,'acquisition_month':dt.month,'acquisition_hour_utc':dt.hour,'frp_mw':frp,'confidence_raw':raw or None,'confidence_native_category':native,'scan_km':scan,'track_km':track,'daynight':dn or None,'processing_version':version,'processing_type':('unknown' if sat=='NOAA-20' and processing(version)=='standard' else processing(version)),'brightness_modis_k':mb,'brightness_viirs_i4_k':i4,'brightness_viirs_i5_k':i5,'fire_type':fire_type,'source_classification':classification,'ingestion_timestamp':stamp,'quality_flags':missing,'raw_record_json':raw_json}

def dumps(value):return json.dumps(value,indent=2,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n'
def write_json(path,obj):Path(path).write_text(dumps(obj),encoding='utf-8')

def ingest(input_dir,output_dir,classification='real',bbox=BBOX,boundary_path=None):
    if classification not in ('real','synthetic'):raise ValueError('invalid classification')
    input_dir=Path(input_dir).resolve();output_dir=Path(output_dir).resolve()
    boundary=None;boundary_hash=None;boundary_bytes=None
    if boundary_path is not None:
        from shapely.geometry import shape
        boundary_bytes=Path(boundary_path).read_bytes();boundary_hash=sha(boundary_bytes)
        if boundary_hash!=OFFICIAL_BOUNDARY_SHA256:raise ValueError('boundary hash does not match reviewed Hawaii GIS file')
        geo=json.loads(boundary_bytes)
        features=geo.get('features',[])
        if geo.get('type')!='FeatureCollection' or len(features)!=1 or features[0].get('properties',{}).get('isle')!='Maui' or features[0].get('properties',{}).get('water')!=0:raise ValueError('invalid Maui boundary identity')
        boundary=shape(features[0]['geometry'])
        if not boundary.is_valid or boundary.geom_type not in ('Polygon','MultiPolygon') or boundary.is_empty:raise ValueError('invalid Maui boundary geometry')
        west,south,east,north=boundary.bounds
        if not (-157<west<east<-155 and 20<south<north<22):raise ValueError('boundary CRS or bounds invalid')
    geographic_filter='maui_coastline_covers' if boundary is not None else 'provisional_bbox_only'
    if output_dir==input_dir or input_dir in output_dir.parents or output_dir in input_dir.parents:raise ValueError('input and output must not overlap')
    files=sorted((p for p in input_dir.rglob('*') if p.is_file() and not p.is_symlink() and p.suffix.lower() in ('.csv','.zip')),key=lambda p:str(p).lower()) if input_dir.exists() else []
    stamp=datetime.now(timezone.utc).isoformat();accepted=[];rejected=[];excluded=[];duplicates=[];sources=[];seen={};file_errors=[]
    counts={'received':0,'accepted':0,'rejected':0,'geographic_excluded':0,'temporal_excluded':0,'duplicates':0}
    for file in files:
        contents=file.read_bytes();file_hash=sha(contents);relative=file.relative_to(input_dir).as_posix()
        try:
            for member,data in read_sources(file):
                sid=sha((file_hash+'\n'+member+'\n'+sha(data)).encode()); meta={'id':sid,'file':relative,'archive_member':member if file.suffix.lower()=='.zip' else None,'sha256':file_hash,'member_sha256':sha(data),'size_bytes':len(contents)};sources.append(meta)
                try:
                    content=data.decode('utf-8-sig');lines=content.splitlines()
                    reader=csv.DictReader(io.StringIO(content,newline=''),strict=True)
                    if not reader.fieldnames:raise ValueError('empty file or missing header')
                    reader.fieldnames=[x.strip().lower() for x in reader.fieldnames]
                    if len(reader.fieldnames)!=len(set(reader.fieldnames)):raise ValueError('duplicate column names')
                    rows=[];previous=reader.line_num
                    for row in reader:
                        start=previous+1
                        while start<=len(lines) and not lines[start-1].strip():start+=1
                        rows.append((start,row));previous=reader.line_num
                    if any(None in row for _,row in rows):raise ValueError('malformed CSV row')
                    sensor=identify(reader.fieldnames,[row for _,row in rows])
                except (UnicodeError,csv.Error,ValueError) as exc:
                    file_errors.append({'file':relative,'member':member,'reason':str(exc)});continue
                for n,row in rows:
                    counts['received']+=1
                    try:obs=normalize(row,sensor,sid,n,classification,stamp)
                    except (ValueError,TypeError,OverflowError) as exc:
                        counts['rejected']+=1;rejected.append({'source_file_id':sid,'source_row_number':n,'reason':str(exc),'raw_record_json':json.dumps(row,ensure_ascii=False,sort_keys=True)});continue
                    if not (bbox[0]<=obs['longitude']<=bbox[2] and bbox[1]<=obs['latitude']<=bbox[3]):
                        counts['geographic_excluded']+=1;excluded.append({'source_file_id':sid,'source_row_number':n,'reason':'outside bbox','raw_record_json':obs['raw_record_json']});continue
                    if boundary is not None:
                        from shapely.geometry import Point
                        if not boundary.covers(Point(obs['longitude'],obs['latitude'])):
                            counts['geographic_excluded']+=1;excluded.append({'source_file_id':sid,'source_row_number':n,'reason':'outside Maui coastline','raw_record_json':obs['raw_record_json']});continue
                    dt=datetime.fromisoformat(obs['acquisition_datetime_utc'])
                    if not START<=dt.date()<=END:
                        counts['temporal_excluded']+=1;excluded.append({'source_file_id':sid,'source_row_number':n,'reason':'outside study period UTC','raw_record_json':obs['raw_record_json']});continue
                    oid=obs['observation_id']
                    if oid in seen:counts['duplicates']+=1;duplicates.append({'observation_id':oid,'source_file_id':sid,'source_row_number':n,'original_source_file_id':seen[oid]});continue
                    seen[oid]=sid;obs['partition']=partition(dt);accepted.append(obs);counts['accepted']+=1
        except (UnsafeArchive,zipfile.BadZipFile,OSError) as exc:file_errors.append({'file':relative,'reason':str(exc)})
    if counts['received']!=sum(counts[k] for k in ('accepted','rejected','geographic_excluded','temporal_excluded','duplicates')):raise ValueError('record counts do not reconcile')
    accepted.sort(key=lambda x:(x['acquisition_datetime_utc'],x['observation_id']))
    parts={p:sum(o['partition']==p for o in accepted) for p in ('training','validation','test')}
    versions=sorted({o['processing_version'] or 'unknown' for o in accepted});types=sorted({o['processing_type'] for o in accepted})
    warnings=[]
    if len(versions)>1:warnings.append('Mixed processing versions; do not assume comparability.')
    if len(types)>1:warnings.append('Mixed processing types; analyze separately and do not silently combine.')
    if 'unknown' in types:warnings.append('Processing type unknown for at least one record.')
    if any(o['satellite']=='NOAA-20' and o['processing_type']=='unknown' for o in accepted):warnings.append('NOAA-20 processing type unresolved: FIRMS README says standard product unavailable despite archive naming; verify with NASA.')
    if any(o['sensor']=='VIIRS' and 'bright_t31' in json.loads(o['raw_record_json']) for o in accepted):warnings.append('VIIRS archive bright_t31 field retained raw; its mapping to I-5 is not independently confirmed.')
    manifest={'schema_version':'1.0','dataset_id':sha(dumps({'sources':sorted(x['id'] for x in sources),'classification':classification,'bbox':list(bbox),'boundary_sha256':boundary_hash,'period':[START.isoformat(),END.isoformat()],'pipeline_version':'0.2.0'}).encode()),'pipeline_version':'0.2.0','classification':classification,'source_organization':'NASA FIRMS (operator asserted)' if classification=='real' else 'synthetic fixture','source_urls':[],'sources':sources,'counts':counts,'partitions':parts,'processing_versions':versions,'processing_types':types,'processing_timestamp_utc':stamp,'coordinate_reference_system':'EPSG:4326','bbox':list(bbox),'geographic_filter':geographic_filter,'boundary_sha256':boundary_hash,'boundary_source':'https://geodata.hawaii.gov/arcgis/rest/services/Terrestrial/MapServer/3' if boundary is not None else None,'study_period_utc':[START.isoformat(),END.isoformat()],'limitations':(['Maui coastline derived from 1983 USGS data; geometry is not a legal survey boundary.'] if boundary is not None else ['Provisional bounding box only; ocean and neighboring land may be included.'])+['Source authenticity not verified by ingestion.','Detections are not incidents and missing detections do not establish absence of fire.','No cross-sensor harmonization.'],'file_errors':file_errors,'warnings':warnings,'acquisition_range_utc':[accepted[0]['acquisition_datetime_utc'],accepted[-1]['acquisition_datetime_utc']] if accepted else None}
    sensor_counts=dict(Counter(o['sensor'] for o in accepted));sat_counts=dict(Counter(o['satellite'] for o in accepted));years=dict(Counter(str(o['acquisition_year']) for o in accepted));months=dict(Counter(o['acquisition_date_utc'][:7] for o in accepted))
    missing=dict(Counter(f for o in accepted for f in o['quality_flags']));confidence={s:dict(Counter(o['confidence_raw'] or 'missing' for o in accepted if o['sensor']==s)) for s in sensor_counts}
    frp={s:{'count':len(v),'min':min(v) if v else None,'max':max(v) if v else None,'mean':sum(v)/len(v) if v else None} for s in sensor_counts for v in [[o['frp_mw'] for o in accepted if o['sensor']==s and o['frp_mw'] is not None]]}
    report={'counts':counts,'partitions':parts,'files_discovered':len(files),'file_errors':file_errors,'sensors':sensor_counts,'satellites':sat_counts,'years':years,'months_utc':months,'missing_optional':missing,'confidence_by_sensor':confidence,'frp_by_sensor_mw':frp,'processing_versions':versions,'processing_types':types,'years_without_detections':[y for y in range(2013,2024) if str(y) not in years],'coverage_note':'No detections do not establish no fire or complete sensor coverage.','geographic_filter':geographic_filter,'limitations':manifest['limitations'],'warnings':warnings}
    output_dir.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.fireready-stage-',dir=output_dir.parent));backup=None
    try:
        import pandas as pd
        if boundary_bytes is not None:(stage/'maui_boundary.geojson').write_bytes(boundary_bytes)
        # Explicit columns ensure valid empty Parquet files.
        cols=['observation_id','source_file_id','source_row_number','source_product','sensor','satellite','latitude','longitude','acquisition_datetime_utc','acquisition_date_utc','local_datetime','local_date','acquisition_year','acquisition_month','acquisition_hour_utc','frp_mw','confidence_raw','confidence_native_category','scan_km','track_km','daynight','processing_version','processing_type','brightness_modis_k','brightness_viirs_i4_k','brightness_viirs_i5_k','fire_type','source_classification','ingestion_timestamp','quality_flags','raw_record_json','partition']
        df=pd.DataFrame(accepted,columns=cols)
        df['acquisition_datetime_utc']=pd.to_datetime(df['acquisition_datetime_utc'],utc=True)
        df['local_datetime']=pd.to_datetime(df['local_datetime'],utc=True).dt.tz_convert('Pacific/Honolulu')
        df['ingestion_timestamp']=pd.to_datetime(df['ingestion_timestamp'],utc=True)
        df.to_parquet(stage/'normalized_observations.parquet',index=False)
        for p in parts:df[df['partition']==p].to_parquet(stage/(p+'_observations.parquet'),index=False)
        pd.DataFrame(rejected,columns=['source_file_id','source_row_number','reason','raw_record_json']).to_parquet(stage/'rejected_observations.parquet',index=False)
        pd.DataFrame(excluded,columns=['source_file_id','source_row_number','reason','raw_record_json']).to_parquet(stage/'excluded_observations.parquet',index=False)
        from jsonschema import validate
        schema_root=Path(__file__).resolve().parent.parent/'schemas'
        validate(manifest,json.loads((schema_root/'pipeline-manifest-v1.schema.json').read_text(encoding='utf-8-sig')))
        write_json(stage/'dataset_manifest.json',manifest);write_json(stage/'data_quality_report.json',report);write_json(stage/'duplicate_lineage.json',duplicates)
        features=[{'type':'Feature','geometry':{'type':'Point','coordinates':[o['longitude'],o['latitude']]},'properties':{'id':o['observation_id'],'sensor':o['sensor'],'satellite':o['satellite'],'acquiredAt':o['acquisition_datetime_utc'],'confidence':o['confidence_raw'],'frpMw':o['frp_mw']}} for o in accepted]
        if len(features)!=counts['accepted'] or len({o['observation_id'] for o in accepted})!=len(accepted):raise ValueError('observation count or identifier error')
        if not all(o['partition']==partition(datetime.fromisoformat(o['acquisition_datetime_utc'])) for o in accepted):raise ValueError('partition mismatch')
        geo={'type':'FeatureCollection','features':features}
        validate(geo,json.loads((schema_root/'hotspots-v1.schema.json').read_text(encoding='utf-8-sig')))
        write_json(stage/'frontend_observations.geojson',geo)
        write_json(stage/'satellite_summary.json',{'sensors':sensor_counts,'satellites':sat_counts});write_json(stage/'temporal_summary.json',{'months_utc':months,'partitions':parts})
        text='# FireReady data quality report\n\n'+f'Classification: {classification}. Geographic filter: {geographic_filter}.\n\n'+''.join(f'- {k}: {v}\n' for k,v in counts.items())+'\n## Warnings and limitations\n\n'+''.join('- '+x+'\n' for x in manifest['limitations'])+f'\nFile errors: {len(file_errors)}. Processing types: {types}. Versions: {versions}.\n'+''.join('- WARNING: '+w+'\n' for w in warnings)
        (stage/'data_quality_report.md').write_text(text,encoding='utf-8')
        import html
        (stage/'data_quality_report.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>FireReady data quality report</title><pre>'+html.escape(text)+'</pre></html>',encoding='utf-8')
        if output_dir.exists():
            backup=output_dir.with_name(output_dir.name+'.previous')
            if backup.exists():raise FileExistsError('backup already exists; resolve it before re-running')
            output_dir.rename(backup)
        try:stage.rename(output_dir)
        except Exception:
            if backup:backup.rename(output_dir)
            raise
        if backup:shutil.rmtree(backup)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return report
