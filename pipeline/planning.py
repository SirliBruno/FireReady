"""Generate land grid and train-only exploratory demand for the Maui MVP."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import Counter
import json,math,hashlib
from shapely.geometry import shape,box,mapping,Point
from shapely.ops import transform
from pyproj import Transformer

def run(root):
    root=Path(root);boundary=root/'data/boundaries/maui-coastline.geojson'
    if hashlib.sha256(boundary.read_bytes()).hexdigest()!='5f918822bb2e523924c9bc917afe81af3491efa43c80388b7bbf3ce4d1b35d7c':raise ValueError('boundary hash mismatch')
    geo=json.loads(boundary.read_text(encoding='utf-8')); forward=Transformer.from_crs(4326,32604,always_xy=True);back=Transformer.from_crs(32604,4326,always_xy=True)
    island=transform(forward.transform,shape(geo['features'][0]['geometry']));x0,y0,x1,y1=island.bounds;grid=[]
    for x in range(math.floor(x0/1000),math.ceil(x1/1000)):
        for y in range(math.floor(y0/1000),math.ceil(y1/1000)):
            cut=box(x*1000,y*1000,(x+1)*1000,(y+1)*1000).intersection(island)
            if cut.is_empty or cut.area<=0:continue
            point=cut.representative_point();lng,lat=back.transform(point.x,point.y)
            grid.append({'id':f'1000:{x}:{y}','area_m2':cut.area,'longitude':lng,'latitude':lat,'x':point.x,'y':point.y,'geometry':mapping(transform(back.transform,cut))})
    stations=[];raw=json.loads((root/'data/auxiliary/fire_stations_statewide.geojson').read_text(encoding='utf-8'))
    for f in raw['features']:
        if f['properties']['island']!='Maui' or f['properties']['status']!='professional':continue
        lng,lat=f['geometry']['coordinates'];x,y=forward.transform(lng,lat)
        if not island.buffer(500).covers(Point(x,y)):continue
        stations.append({'id':str(f['properties']['objectid']),'name':f['properties']['name'],'longitude':lng,'latitude':lat,'x':x,'y':y})
    stations.sort(key=lambda x:x['id']);reference=json.loads((root/'public/data/research/harmonization.json').read_text(encoding='utf-8'));days=set()
    for f in reference['observations']['features']:
        p=f['properties']
        if p['partition']!='training':continue
        day=datetime.fromisoformat(p['acquiredAt']).astimezone(ZoneInfo('Pacific/Honolulu')).date().isoformat();days.add((p['gridId'],day))
    counts=Counter((cell,int(day[5:7])) for cell,day in days)
    model={'version':'1.0','cohort':'MODIS + Suomi NPP','training':'UTC partitions 2013–2020','feature':'local active cell-days','weights':'count / 8 calendar training years; not coverage adjusted','priority':'100 * cell monthly count / maximum monthly training cell count, exploratory','cost':'EPSG:32604 straight-line km, not driving or emergency response time','holdout':'2023 descriptive results previously exposed; not blinded','dataset_id':reference['report']['dataset_id']}
    model_id=hashlib.sha256(json.dumps(model,sort_keys=True).encode()).hexdigest()
    output={'model':model,'model_id':model_id,'region':'maui','stations':stations,'grid':grid,'monthly_weights':{str(m):[counts[(c['id'],m)]/8 for c in grid] for m in range(1,13)},'costs_km':[[round(math.hypot(s['x']-c['x'],s['y']-c['y'])/1000,5) for c in grid] for s in stations],'station_source':'https://geodata.hawaii.gov/arcgis/rest/services/EmergMgmtPubSafety/MapServer/7','station_retrieved':'2026-11-14','station_limitations':'2025 source collection; historical 2023 status and vehicle inventories unverified','evidence':'exploratory; observation opportunities unknown; unobserved cells are not safe'}
    dest=root/'public/data/planning';dest.mkdir(parents=True,exist_ok=True);(dest/'maui.json').write_text(json.dumps(output,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    return {'cells':len(grid),'stations':len(stations),'model_id':model_id,'training_cell_days':len(days)}
if __name__=='__main__':print(json.dumps(run(Path.cwd()),indent=2))
