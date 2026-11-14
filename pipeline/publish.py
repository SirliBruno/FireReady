"""Explicit, reviewer-authorized publishing of sanitized real outputs only."""
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
import hashlib, json, os, re, tempfile

def publish(source,destination,*,reviewer,evidence,source_url,raw_root=None):
    source=Path(source);destination=Path(destination)
    manifest=json.loads((source/'dataset_manifest.json').read_text(encoding='utf-8'))
    if manifest.get('classification')!='real':raise ValueError('synthetic outputs cannot be published as real')
    if not reviewer.strip() or any(urlparse(url).scheme not in ('http','https') or not urlparse(url).netloc for url in (evidence,source_url)):raise ValueError('reviewer and HTTP(S) evidence and source URLs are required')
    if manifest.get('schema_version')!='1.0' or not re.fullmatch(r'[0-9a-f]{64}',str(manifest.get('dataset_id',''))) or not isinstance(manifest.get('sources'),list) or not manifest['sources'] or not isinstance(manifest.get('counts'),dict):raise ValueError('invalid manifest')
    counts=manifest['counts'];keys=('accepted','rejected','geographic_excluded','temporal_excluded','duplicates')
    if any(not isinstance(counts.get(k),int) or counts[k]<0 for k in (*keys,'received')) or counts['received']!=sum(counts[k] for k in keys):raise ValueError('invalid manifest counts')
    if manifest.get('file_errors') or not counts['accepted']:raise ValueError('cannot publish empty or file-error datasets')
    if len(set(manifest.get('processing_types',[])))>1:raise ValueError('mixed processing types must be separated before publishing')
    if raw_root is None:raise ValueError('raw source directory is required for hash verification')
    root=Path(raw_root).resolve()
    for item in manifest['sources']:
        if not isinstance(item,dict) or not re.fullmatch(r'[0-9a-f]{64}',str(item.get('sha256',''))):raise ValueError('invalid source hash')
        path=(root/str(item.get('file',''))).resolve()
        if root not in path.parents or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('source missing, outside raw directory, or hash changed')
    import pandas as pd
    df=pd.read_parquet(source/'normalized_observations.parquet')
    if len(df)!=manifest['counts']['accepted'] or not (df['source_classification']=='real').all():raise ValueError('dataset and manifest do not agree')
    dates=pd.to_datetime(df['local_date']);series=dates.dt.strftime('%Y-%m').value_counts().sort_index()
    observations=[{'year':int(k[:4]),'month':int(k[5:]),'count':int(v)} for k,v in series.items()]
    start,end=manifest['acquisition_range_utc'];stamp=datetime.now(timezone.utc).isoformat();products=sorted(set(df['source_product']));sensors=sorted(set(df['sensor']));satellites=sorted(set(df['satellite']))
    provenance={'sourceOrganization':'NASA FIRMS (operator reviewed)','productName':', '.join(products),'sensor':', '.join(sensors),'satellite':', '.join(satellites),'processingVersion':', '.join(manifest['processing_versions']),'acquisitionTimeRange':[start,end],'geographicExtent':manifest['bbox'],'processingDate':manifest['processing_timestamp_utc'],'recordCount':len(observations),'units':{'count':'thermal detections'},'limitations':manifest['limitations']+manifest.get('warnings',[]),'classification':'real'}
    bundle={'schemaVersion':'1.0','classification':'real','provenance':provenance,'review':{'reviewer':reviewer,'evidence':evidence,'reviewedAt':stamp},'observations':observations}
    manifest['source_urls']=[source_url]
    geo=json.loads((source/'frontend_observations.geojson').read_text(encoding='utf-8'))
    if geo.get('type')!='FeatureCollection' or len(geo.get('features',[]))!=len(df):raise ValueError('spatial output and manifest do not agree')
    try:
        records={str(row['observation_id']):row for _,row in df.iterrows()}
        ids=set(records)
        if len(ids)!=len(df):raise ValueError('duplicate identifiers')
        feature_ids=[]
        for feature in geo['features']:
            coords=feature['geometry']['coordinates'];props=feature['properties']
            if feature['type']!='Feature' or feature['geometry']['type']!='Point' or len(coords)!=2 or not -180<=coords[0]<=180 or not -90<=coords[1]<=90 or props['sensor'] not in ('MODIS','VIIRS') or props['id'] not in ids:raise ValueError('invalid spatial feature')
            record=records[props['id']];feature_ids.append(props['id'])
            if coords!=[record['longitude'],record['latitude']] or props['sensor']!=record['sensor'] or props['satellite']!=record['satellite'] or pd.to_datetime(props['acquiredAt'],utc=True)!=record['acquisition_datetime_utc']:raise ValueError('spatial feature differs from normalized record')
        if len(set(feature_ids))!=len(ids):raise ValueError('invalid spatial feature identifiers')
    except (TypeError,KeyError,IndexError) as exc:raise ValueError('invalid spatial output') from exc
    destination.mkdir(parents=True,exist_ok=True)
    def atomic(name,value):
        fd,temp=tempfile.mkstemp(prefix='.fireready-',suffix='.tmp',dir=destination)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,allow_nan=False);f.write('\n')
            os.replace(temp,destination/name)
        finally:
            if os.path.exists(temp):os.unlink(temp)
    atomic('status.json',{'available':False})
    atomic('dataset.json',bundle);atomic('manifest.json',manifest);atomic('observations.geojson',geo)
    atomic('status.json',{'available':True})
