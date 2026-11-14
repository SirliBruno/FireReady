"""Descriptive local-calendar analysis of the frozen Maui research cohort.

No zero-fire inference, coverage adjustment, priority, or demand is produced.
UTC-derived partitions are retained even if a local calendar day crosses a split.
"""
from collections import Counter,defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import hashlib,json

ZONE=ZoneInfo('Pacific/Honolulu')

def aggregate_local_days(features):
    groups=defaultdict(list)
    for feature in features:
        p=feature['properties']
        local=datetime.fromisoformat(p['acquiredAt'].replace('Z','+00:00')).astimezone(ZONE)
        groups[(p['partition'],p['gridId'],local.date().isoformat())].append(p)
    result=[]
    for (partition,cell,local_date),items in sorted(groups.items()):
        result.append({'partition':partition,'grid_cell_id':cell,'local_date':local_date,'observation_count':len(items),'sensors':sorted({p['sensor'] for p in items}),'source_observation_ids':sorted(p['id'] for p in items)})
    return result

def run(root:Path, region='maui'):
    if region not in ('maui','all'): raise ValueError('Only Maui has a configured and processed reference cohort')
    source=root/'data/processed/harmonization/real/artifacts/research_preview.json'
    lockpath=root/'data/processed/harmonization/real/harmonization_config.lock.json'
    source_bytes=source.read_bytes(); data=json.loads(source_bytes); lock=json.loads(lockpath.read_text(encoding='utf-8'))
    if data['report']['dataset_id']!=lock['dataset_id'] or data['report']['configuration_sha256']!=lock['configuration_sha256']:
        raise ValueError('Research preview does not match frozen harmonization configuration')
    features=data['observations']['features']; rows=aggregate_local_days(features)
    months=defaultdict(lambda:defaultdict(int)); yearly=Counter(); sensor=Counter(); years=defaultdict(set)
    for f in features:
        p=f['properties'];sensor[p['sensor']]+=1; yearly[datetime.fromisoformat(p['acquiredAt']).astimezone(ZONE).year]+=1
    for row in rows:
        local=row['local_date']; key=local[:7]; months[key][row['grid_cell_id']]+=1;years[int(local[5:7])].add(local[:4])
    grid_ids={f['properties']['grid_cell_id'] for f in data['grid']['features']}
    if any(row['grid_cell_id'] not in grid_ids for row in rows): raise ValueError('Observation references missing grid cell')
    calendar=[]
    for month in range(1,13):
        matching=[r for r in rows if int(r['local_date'][5:7])==month]
        calendar.append({'month':month,'active_cell_days':len(matching),'years_with_observations':len(years[month]),'active_cells':len({r['grid_cell_id'] for r in matching})})
    output={'schema_version':'1.0','region':{'id':'maui','name_ar':'ماوي، هاواي','timezone':'Pacific/Honolulu'},'source_dataset_id':lock['dataset_id'],'harmonization_configuration_id':lock['configuration_sha256'],'source_preview_sha256':hashlib.sha256(source_bytes).hexdigest(),'classification':'real-unverified','coverage':'unknown','evidence_quality':'insufficient for operational priorities','limitations':['Unknown satellite observation opportunities and clouds; missing detections are not confirmed absence.','Only MODIS and Suomi NPP reference cohort; NOAA-20 excluded due to unresolved processing.','User-supplied source authenticity is not independently verified.','2023 descriptive totals were seen before harmonization freeze; not fully blinded.','Grid contains only cells ever observed in 2013–2023; it is not the full eligible land area.','Local cell-days reconstructed from observation timestamps are distinct from UTC cell-days; UTC partition labels retained.'],'observation_count':len(features),'cell_day_count':len(rows),'observed_cells':len(grid_ids),'sensor_counts':dict(sensor),'year_counts':dict(sorted(yearly.items())),'calendar':calendar,'monthly_cells':{k:dict(sorted(v.items())) for k,v in sorted(months.items())},'grid':data['grid']}
    dest=root/'data/processed/seasonal/maui';dest.mkdir(parents=True,exist_ok=True)
    (dest/'local_cell_days.json').write_text(json.dumps(rows,ensure_ascii=False,sort_keys=True),encoding='utf-8')
    encoded=json.dumps(output,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    (dest/'regional_summary.json').write_text(encoded,encoding='utf-8')
    public=root/'public/data/seasonal';public.mkdir(parents=True,exist_ok=True)
    (public/'maui.json').write_text(encoded,encoding='utf-8')
    return {'region':'maui','observations':len(features),'local_cell_days':len(rows),'observed_cells':len(grid_ids),'bytes':len(encoded.encode('utf-8'))}
