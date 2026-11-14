"""Centroid-based, exploratory active-fire co-observation analysis, not incident inference."""
from __future__ import annotations
from collections import Counter,defaultdict
from dataclasses import dataclass,asdict
from datetime import datetime,timezone,timedelta
from statistics import median
import hashlib,json,math

@dataclass(frozen=True)
class Config:
    grid_m:int=1000
    distance_m:int=1000
    window_minutes:int=60
    quality:str='all'
    cohort:str='reference'
    crs:str='EPSG:32604'
    binning:str='UTC day'

def config_hash(c):
    return hashlib.sha256(json.dumps(asdict(c),sort_keys=True,separators=(',',':')).encode()).hexdigest()

def assign_cell(x,y,resolution):
    if resolution<=0:raise ValueError('grid size must be positive')
    return f'{resolution}:{math.floor(x/resolution)}:{math.floor(y/resolution)}'

def quality_pass(o,profile):
    if profile=='all':return True
    if profile!='conservative':raise ValueError('unknown quality profile')
    value=o.get('confidence_raw')
    if value is None or str(value).strip()=='':return False
    if o['sensor']=='MODIS':
        try:return float(value)>=30
        except (ValueError,TypeError):return False
    return str(value).lower() in ('n','h')

def cohort_pass(o,cohort):
    if cohort=='reference':return o['sensor']=='MODIS' or o['satellite']=='Suomi NPP'
    if cohort=='all':return o['sensor'] in ('MODIS','VIIRS')
    raise ValueError('unknown satellite cohort')

def time_value(x):
    if isinstance(x,datetime):
        if x.tzinfo is None:raise ValueError('naive datetime')
        return x.astimezone(timezone.utc)
    dt=datetime.fromisoformat(str(x).replace('Z','+00:00'))
    if dt.tzinfo is None:raise ValueError('naive datetime')
    return dt.astimezone(timezone.utc)

def match_candidates(rows,config):
    if config.distance_m<=0 or config.window_minutes<0:raise ValueError('invalid match threshold')
    viirs=defaultdict(list);size=config.distance_m
    for o in rows:
        if o['sensor']=='VIIRS':viirs[(o['partition'],math.floor(o['x']/size),math.floor(o['y']/size))].append(o)
    candidates=[];degree_m=Counter();degree_v=Counter()
    for m in rows:
        if m['sensor']!='MODIS':continue
        bx=math.floor(m['x']/size);by=math.floor(m['y']/size);tm=time_value(m['acquisition_datetime_utc'])
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                for v in viirs.get((m['partition'],bx+dx,by+dy),[]):
                    distance=math.hypot(m['x']-v['x'],m['y']-v['y'])
                    if distance>config.distance_m:continue
                    delta=abs((tm-time_value(v['acquisition_datetime_utc'])).total_seconds())
                    if delta>config.window_minutes*60:continue
                    degree_m[m['observation_id']]+=1;degree_v[v['observation_id']]+=1
                    candidates.append({'modis_id':m['observation_id'],'viirs_id':v['observation_id'],'distance_m':distance,'time_difference_minutes':delta/60,'partition':m['partition']})
    for c in candidates:c['ambiguous']=degree_m[c['modis_id']]>1 or degree_v[c['viirs_id']]>1
    return sorted(candidates,key=lambda c:(c['modis_id'],c['viirs_id']))

def aggregate_units(rows,pairs,config):
    by_id={o['observation_id']:o for o in rows}; matched_m={p['modis_id'] for p in pairs};matched_v={p['viirs_id'] for p in pairs};groups=defaultdict(list);edge_counts=Counter()
    for o in rows:
        t=time_value(o['acquisition_datetime_utc']);key=(o['partition'],assign_cell(o['x'],o['y'],config.grid_m),t.date().isoformat());groups[key].append(o)
    for p in pairs:
        m=by_id[p['modis_id']];key=(m['partition'],assign_cell(m['x'],m['y'],config.grid_m),time_value(m['acquisition_datetime_utc']).date().isoformat());edge_counts[key]+=1
    result=[]
    for (part,cell,day),items in sorted(groups.items()):
        count=Counter(o['sensor'] for o in items);satellites=Counter(o['satellite'] for o in items);quality={};frp={}
        for sensor in ('MODIS','VIIRS'):
            sel=[o for o in items if o['sensor']==sensor];quality[sensor]=dict(Counter(str(o.get('confidence_raw') or 'missing') for o in sel));values=[float(o['frp_mw']) for o in sel if o.get('frp_mw') is not None and math.isfinite(float(o['frp_mw']))];frp[sensor]={'n':len(values),'median_mw':median(values) if values else None}
        result.append({'partition':part,'grid_cell_id':cell,'time_bin_start':day+'T00:00:00+00:00','time_bin_end':(datetime.fromisoformat(day)+timedelta(days=1)).isoformat()+'+00:00','year':int(day[:4]),'month':int(day[5:7]),'sensor_presence':sorted(count),'modis_detection_count':count['MODIS'],'viirs_detection_count':count['VIIRS'],'satellite_detection_counts':dict(satellites),'total_source_observations':len(items),'potential_cross_sensor_matches':edge_counts[(part,cell,day)],'unmatched_modis_observations':sum(o['sensor']=='MODIS' and o['observation_id'] not in matched_m for o in items),'unmatched_viirs_observations':sum(o['sensor']=='VIIRS' and o['observation_id'] not in matched_v for o in items),'native_quality_summaries':quality,'sensor_specific_frp_summaries':frp,'uncertainty_flags':['centroid assignment','coverage unknown','not a fire incident'],'source_observation_references':sorted(o['observation_id'] for o in items),'harmonization_configuration_id':config_hash(config)})
    return result

def freeze_reference(input_dir,output_dir):
    """Write once before sensitivity or test evaluation; no test records are read."""
    from pathlib import Path
    from datetime import datetime,timezone
    source=Path(input_dir);out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((source/'dataset_manifest.json').read_text(encoding='utf-8'))
    if manifest.get('classification')!='real' or manifest.get('file_errors'):raise ValueError('a real-classified, error-free ingestion is required')
    cfg=Config(); lock={'schema_version':'1.0','config':asdict(cfg),'configuration_sha256':config_hash(cfg),'dataset_id':manifest['dataset_id'],'partition_file_sha256':{p:hashlib.sha256((source/(p+'_observations.parquet')).read_bytes()).hexdigest() for p in ('training','validation','test')},'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'selection':'Pre-specified 1 km grid, 1 km centroid tolerance, 60 min, all valid, MODIS and Suomi NPP; not optimized for agreement.','holdout_disclosure':'Descriptive 2023 totals had been visible during ingestion audit before this freeze. No 2023 record was used to select the thresholds; this is not a fully blinded pre-registration.','coverage':'Unknown; no absence means failure inference.'}
    path=out/'harmonization_config.lock.json'
    with path.open('x',encoding='utf-8') as f:json.dump(lock,f,indent=2,ensure_ascii=False,sort_keys=True);f.write('\n')
    return lock

def load_lock(input_dir,output_dir):
    from pathlib import Path
    source=Path(input_dir);lock=json.loads((Path(output_dir)/'harmonization_config.lock.json').read_text(encoding='utf-8'));manifest=json.loads((source/'dataset_manifest.json').read_text(encoding='utf-8'))
    cfg=Config(**lock['config'])
    if lock['configuration_sha256']!=config_hash(cfg) or lock['dataset_id']!=manifest['dataset_id']:raise ValueError('configuration lock or input dataset changed')
    if manifest.get('boundary_sha256') and hashlib.sha256((source/'maui_boundary.geojson').read_bytes()).hexdigest()!=manifest['boundary_sha256']:raise ValueError('boundary file changed')
    for part,digest in lock['partition_file_sha256'].items():
        if hashlib.sha256((source/(part+'_observations.parquet')).read_bytes()).hexdigest()!=digest:raise ValueError('locked partition file changed')
    return cfg,lock,manifest

def read_partition(source,part):
    import pandas as pd
    from pyproj import Transformer
    frame=pd.read_parquet(source/(part+'_observations.parquet'))
    if not frame.empty and not (frame['partition']==part).all():raise ValueError('partition mismatch in source')
    if not frame.empty and any((r=='training' and not 2013<=int(y)<=2020) or (r=='validation' and not 2021<=int(y)<=2022) or (r=='test' and int(y)!=2023) for r,y in zip(frame['partition'],frame['acquisition_year'])):raise ValueError('year outside partition')
    transformer=Transformer.from_crs('EPSG:4326','EPSG:32604',always_xy=True);rows=[]
    for item in frame.to_dict('records'):
        x,y=transformer.transform(item['longitude'],item['latitude']);item['x']=x;item['y']=y
        if pd.isna(item['frp_mw']):item['frp_mw']=None
        rows.append(item)
    return rows

def descriptive(rows,pairs,cfg):
    modis={o['observation_id'] for o in rows if o['sensor']=='MODIS'};viirs={o['observation_id'] for o in rows if o['sensor']=='VIIRS'};mm={p['modis_id'] for p in pairs};mv={p['viirs_id'] for p in pairs}
    cells={s:{(assign_cell(o['x'],o['y'],cfg.grid_m),time_value(o['acquisition_datetime_utc']).date().isoformat()) for o in rows if o['sensor']==s} for s in ('MODIS','VIIRS')};both=cells['MODIS']&cells['VIIRS'];union=cells['MODIS']|cells['VIIRS']
    return {'input_observations':len(rows),'modis_observations':len(modis),'viirs_observations':len(viirs),'potential_pair_edges':len(pairs),'matched_modis_observations':len(mm),'matched_viirs_observations':len(mv),'unmatched_modis_observations':len(modis-mm),'unmatched_viirs_observations':len(viirs-mv),'active_grid_cell_days':len(union),'modis_positive_grid_cell_days':len(cells['MODIS']),'viirs_positive_grid_cell_days':len(cells['VIIRS']),'both_positive_grid_cell_days':len(both),'positive_grid_day_jaccard':len(both)/len(union) if union else None,'active_grid_cell_days_by_utc_month':dict(Counter(day[5:7] for _,day in union)),'distance_m_median':median([p['distance_m'] for p in pairs]) if pairs else None,'time_minutes_median':median([p['time_difference_minutes'] for p in pairs]) if pairs else None,'denominator':'Union of sensor-positive UTC grid-cell days; no detection opportunity or negative ground truth assumed.'}

def sensitivity(rows):
    if any(o.get('partition') not in ('training','validation') or time_value(o['acquisition_datetime_utc']).year>=2023 for o in rows):raise ValueError('held-out or invalid partition supplied to sensitivity')
    from itertools import product
    maximal=match_candidates(rows,Config(distance_m=2000,window_minutes=1440,cohort='all'))
    results=[]
    for grid,distance,window,quality,cohort in product((500,1000,2000),(500,1000,2000),(30,60,180,360,1440),('all','conservative'),('reference','all')):
        cfg=Config(grid_m=grid,distance_m=distance,window_minutes=window,quality=quality,cohort=cohort)
        selected=[r for r in rows if cohort_pass(r,cohort) and quality_pass(r,quality)];ids={r['observation_id'] for r in selected}
        pairs=[p for p in maximal if p['modis_id'] in ids and p['viirs_id'] in ids and p['distance_m']<=distance and p['time_difference_minutes']<=window]
        row={'config':asdict(cfg),'configuration_sha256':config_hash(cfg)}
        for part in ('training','validation'):
            subset=[r for r in selected if r['partition']==part];edges=[p for p in pairs if p['partition']==part];row[part]=descriptive(subset,edges,cfg)
        results.append(row)
    return results

def run_harmonization(input_dir,output_dir):
    """Read a frozen configuration, run train/validation sensitivity, then held-out analysis."""
    import os,shutil,tempfile,time
    from pathlib import Path
    import pandas as pd
    from shapely.geometry import shape,box,mapping
    from shapely.ops import transform
    from pyproj import Transformer
    started=time.perf_counter();source=Path(input_dir);out=Path(output_dir);cfg,lock,manifest=load_lock(source,out)
    # Sensitivity only uses training and validation records. Test partition is not read until after this completes.
    pre=read_partition(source,'training')+read_partition(source,'validation');sensitivity_results=sensitivity(pre)
    test=read_partition(source,'test');all_rows=pre+test
    selected=[o for o in all_rows if cohort_pass(o,cfg.cohort) and quality_pass(o,cfg.quality)]
    edges=match_candidates(selected,cfg);by_id={o['observation_id']:o for o in selected}
    for edge in edges:
        m=by_id[edge['modis_id']];v=by_id[edge['viirs_id']]
        edge.update({'modis_satellite':m['satellite'],'viirs_satellite':v['satellite'],'modis_confidence':m['confidence_raw'],'viirs_confidence':v['confidence_raw'],'modis_frp_mw':m['frp_mw'],'viirs_frp_mw':v['frp_mw'],'match_criteria':f'centroid <= {cfg.distance_m} m and UTC delta <= {cfg.window_minutes} min; same partition','configuration_sha256':config_hash(cfg)})
    units=aggregate_units(selected,edges,cfg)
    if sum(u['total_source_observations'] for u in units)!=len(selected):raise ValueError('activity observations failed reconciliation')
    matched={e['modis_id'] for e in edges}|{e['viirs_id'] for e in edges}
    unmatched=[{'observation_id':o['observation_id'],'sensor':o['sensor'],'satellite':o['satellite'],'partition':o['partition'],'reason':'no candidate under configured thresholds; coverage unknown'} for o in selected if o['observation_id'] not in matched]
    summaries={p:descriptive([o for o in selected if o['partition']==p],[e for e in edges if e['partition']==p],cfg) for p in ('training','validation','test')}
    frp={}
    for part in ('training','validation','test'):
        frp[part]={}
        for sensor in ('MODIS','VIIRS'):
            vals=sorted(float(o['frp_mw']) for o in selected if o['partition']==part and o['sensor']==sensor and o.get('frp_mw') is not None)
            frp[part][sensor]={'count':len(vals),'median_mw':median(vals) if vals else None,'min_mw':min(vals) if vals else None,'max_mw':max(vals) if vals else None,'note':'Native sensor summaries only; not combined or energy estimates.'}
    geo=json.loads((source/'maui_boundary.geojson').read_text(encoding='utf-8'));to_utm=Transformer.from_crs('EPSG:4326','EPSG:32604',always_xy=True);to_wgs=Transformer.from_crs('EPSG:32604','EPSG:4326',always_xy=True);island=transform(to_utm.transform,shape(geo['features'][0]['geometry']))
    grid=[]
    for cell in sorted({u['grid_cell_id'] for u in units}):
        size,ix,iy=map(int,cell.split(':'));clipped=box(ix*size,iy*size,(ix+1)*size,(iy+1)*size).intersection(island)
        if clipped.is_empty:raise ValueError('assigned cell does not intersect island polygon')
        grid.append({'type':'Feature','geometry':mapping(transform(to_wgs.transform,clipped)),'properties':{'grid_cell_id':cell,'nominal_grid_m':size,'area_m2':clipped.area,'crs_analysis':'EPSG:32604','configuration_sha256':config_hash(cfg)}})
    annual=[];monthly_local=[]
    for part in ('training','validation','test'):
        subset=[o for o in selected if o['partition']==part]
        for (year,sensor),count in sorted(Counter((time_value(o['acquisition_datetime_utc']).year,o['sensor']) for o in subset).items()):annual.append({'partition':part,'year':year,'sensor':sensor,'observations':count})
        for (month,sensor,satellite),count in sorted(Counter((str(o['local_date'])[:7],o['sensor'],o['satellite']) for o in subset).items()):monthly_local.append({'partition':part,'local_month':month,'sensor':sensor,'satellite':satellite,'observations':count})
    limitation=['Centroid distance and cell assignment approximate pixel footprints; scan and track do not provide orientation.','Pair edges are potential co-observations, not confirmed fires; one-to-many candidate edges are not incident counts.','Unknown observation opportunities, cloud and sensor coverage; unmatched observations are not false negatives.','NOAA-20 excluded from reference cohort because processing type is unresolved; sensitivity contains an all-satellite scenario.','FRP is retained separately by sensor; no cross-sensor sum or fire energy is calculated.','Maui coastline comes from 1983 source geometry and is not a legal boundary.','2023 descriptive counts were visible during the ingestion audit before configuration freeze; evaluation is not fully blinded.']
    report={'schema_version':'1.0','dataset_id':manifest['dataset_id'],'configuration_sha256':config_hash(cfg),'configuration':asdict(cfg),'source_counts':manifest['counts'],'acquisition_range_utc':manifest['acquisition_range_utc'],'satellite_inventory':dict(Counter(o['satellite'] for o in all_rows)),'processing_types':manifest['processing_types'],'selected_reference_count':len(selected),'excluded_from_reference_count':len(all_rows)-len(selected),'partitions':summaries,'sensitivity_configurations':len(sensitivity_results),'external_validation':'Not performed; no independent fire perimeter or incident labels were provided.','limitations':limitation,'processing_elapsed_seconds':None}
    out.mkdir(parents=True,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='.harmonization-',dir=out));destination=out/'artifacts';backup=None
    try:
        def js(name,obj):(stage/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
        parquet_units=[]
        for unit in units:
            copy=dict(unit)
            for key in ('sensor_presence','satellite_detection_counts','native_quality_summaries','sensor_specific_frp_summaries','uncertainty_flags','source_observation_references'):copy[key]=json.dumps(copy[key],ensure_ascii=False,sort_keys=True)
            parquet_units.append(copy)
        unit_columns=['partition','grid_cell_id','time_bin_start','time_bin_end','year','month','sensor_presence','modis_detection_count','viirs_detection_count','satellite_detection_counts','total_source_observations','potential_cross_sensor_matches','unmatched_modis_observations','unmatched_viirs_observations','native_quality_summaries','sensor_specific_frp_summaries','uncertainty_flags','source_observation_references','harmonization_configuration_id']
        udf=pd.DataFrame(parquet_units,columns=unit_columns);udf.to_parquet(stage/'harmonized_activity.parquet',index=False)
        for part in ('training','validation','test'):udf[udf['partition']==part].to_parquet(stage/(part+'_activity.parquet'),index=False)
        pair_cols=['modis_id','viirs_id','distance_m','time_difference_minutes','partition','ambiguous','modis_satellite','viirs_satellite','modis_confidence','viirs_confidence','modis_frp_mw','viirs_frp_mw','match_criteria','configuration_sha256']
        pd.DataFrame(edges,columns=pair_cols).to_parquet(stage/'potential_matches.parquet',index=False)
        pd.DataFrame(unmatched,columns=['observation_id','sensor','satellite','partition','reason']).to_parquet(stage/'unmatched_observations.parquet',index=False)
        js('harmonized_grid.geojson',{'type':'FeatureCollection','features':grid});js('sensor_agreement.json',{'configuration':asdict(cfg),'partitions':summaries});js('frp_analysis.json',frp);js('sensitivity_analysis.json',{'scope':'training and validation only','results':sensitivity_results});js('annual_sensor_summary.json',annual);js('monthly_sensor_local_summary.json',{'timezone':'Pacific/Honolulu','partition_convention':'UTC acquisition year','records':monthly_local})
        report['processing_elapsed_seconds']=round(time.perf_counter()-started,3)
        harm_manifest={'schema_version':'1.0','classification':'real (source asserted, not independently authenticated)','input_dataset_id':manifest['dataset_id'],'configuration_sha256':config_hash(cfg),'configuration_lock':'../harmonization_config.lock.json','boundary_sha256':manifest['boundary_sha256'],'sources':manifest['sources'],'units':len(units),'candidate_pairs':len(edges),'unmatched_observations':len(unmatched),'spatial_crs':'EPSG:32604','geographic_crs':'EPSG:4326','temporal_basis':'UTC calendar day','limitations':limitation}
        js('harmonization_manifest.json',harm_manifest);js('harmonization_report.json',report)
        js('research_summary.json',{'schema_version':'1.0','classification':'real-unverified','report':report,'sources':manifest['sources'],'source_warnings':manifest.get('warnings',[])})
        edge_index=defaultdict(list)
        for e in edges:
            edge_index[e['modis_id']].append({'other_id':e['viirs_id'],'distance_m':round(e['distance_m'],1),'minutes':round(e['time_difference_minutes'],1),'ambiguous':e['ambiguous']})
            edge_index[e['viirs_id']].append({'other_id':e['modis_id'],'distance_m':round(e['distance_m'],1),'minutes':round(e['time_difference_minutes'],1),'ambiguous':e['ambiguous']})
        obs_features=[]
        for o in selected:
            obs_features.append({'type':'Feature','geometry':{'type':'Point','coordinates':[o['longitude'],o['latitude']]},'properties':{'id':o['observation_id'],'sensor':o['sensor'],'satellite':o['satellite'],'acquiredAt':time_value(o['acquisition_datetime_utc']).isoformat(),'confidence':o['confidence_raw'],'frpMw':o['frp_mw'],'scanKm':o['scan_km'],'trackKm':o['track_km'],'gridId':assign_cell(o['x'],o['y'],cfg.grid_m),'partition':o['partition'],'matches':edge_index[o['observation_id']]}})
        display_units=[{k:u[k] for k in ('partition','grid_cell_id','time_bin_start','modis_detection_count','viirs_detection_count','potential_cross_sensor_matches','total_source_observations')} for u in units]
        js('research_preview.json',{'schema_version':'1.0','classification':'real-unverified','label':'User-supplied FIRMS-format data; source not independently authenticated. Research preview, not operational guidance.','report':report,'sources':manifest['sources'],'source_warnings':manifest.get('warnings',[]),'observations':{'type':'FeatureCollection','features':obs_features},'grid':{'type':'FeatureCollection','features':grid},'activity':display_units,'sensitivity':sensitivity_results})
        js('frontend_data_manifest.json',{'schema_version':'1.0','dataset_id':manifest['dataset_id'],'configuration_sha256':config_hash(cfg),'files':['harmonized_grid.geojson','sensor_agreement.json','annual_sensor_summary.json'],'classification':'real-unverified','limitations':limitation})
        lines=['# FireReady harmonization report','','Descriptive research analysis; not a fire incident count.','','Reference configuration: '+json.dumps(asdict(cfg)),f"Source accepted: {manifest['counts']['accepted']}; selected cohort: {len(selected)}; excluded from reference: {len(all_rows)-len(selected)}.",f'Sensitivity scenarios (training/validation only): {len(sensitivity_results)}.','']
        for part,data in summaries.items():lines.append(f"- {part}: {data['input_observations']} observations; {data['potential_pair_edges']} candidate edges; {data['active_grid_cell_days']} active grid-cell days; positive-day Jaccard {data['positive_grid_day_jaccard']}.")
        lines+=['','## Limitations']+['- '+x for x in limitation];(stage/'harmonization_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        if destination.exists():
            backup=out/'artifacts.previous'
            if backup.exists():raise FileExistsError('previous artifacts backup exists')
            destination.rename(backup)
        try:stage.rename(destination)
        except Exception:
            if backup:backup.rename(destination)
            raise
        if backup:shutil.rmtree(backup)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return report

def publish_research_preview(input_dir,output_dir,public_dir,raw_root):
    """Publish a clearly unverified local research preview, never as a reviewed operational dataset."""
    import os,tempfile
    from pathlib import Path
    source=Path(input_dir);out=Path(output_dir);public=Path(public_dir);root=Path(raw_root).resolve()
    cfg,lock,manifest=load_lock(source,out)
    if manifest.get('classification')!='real' or manifest.get('file_errors'):raise ValueError('research preview requires real-classified, error-free input')
    for entry in manifest['sources']:
        path=(root/entry['file']).resolve()
        if root not in path.parents or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('source file missing or changed')
    data=json.loads((out/'artifacts'/'research_preview.json').read_text(encoding='utf-8'))
    if data.get('classification')!='real-unverified' or data.get('report',{}).get('configuration_sha256')!=config_hash(cfg) or data['report'].get('dataset_id')!=manifest['dataset_id']:raise ValueError('research preview provenance mismatch')
    if len(data['observations']['features'])!=data['report']['selected_reference_count']:raise ValueError('research preview observation count mismatch')
    public.mkdir(parents=True,exist_ok=True);research=public/'research';research.mkdir(exist_ok=True)
    def atomic(path,obj):
        fd,tmp=tempfile.mkstemp(prefix='.fireready-',suffix='.tmp',dir=path.parent)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,allow_nan=False);f.write('\n')
            os.replace(tmp,path)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    atomic(public/'research-status.json',{'available':False})
    summary=json.loads((out/'artifacts'/'research_summary.json').read_text(encoding='utf-8'))
    if summary.get('classification')!='real-unverified' or summary.get('report')!=data.get('report') or summary.get('sources')!=data.get('sources'):raise ValueError('research summary provenance mismatch')
    atomic(research/'harmonization.json',data)
    atomic(research/'summary.json',summary)
    atomic(public/'research-status.json',{'available':True,'classification':'real-unverified','dataset_id':manifest['dataset_id']})
    return {'destination':str(research/'harmonization.json'),'classification':'real-unverified','source_authenticity':'not independently authenticated','configuration_sha256':config_hash(cfg)}
