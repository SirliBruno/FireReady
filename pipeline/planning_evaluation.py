from pathlib import Path
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo
import json

def evaluate(root=Path.cwd()):
    data=json.loads((root/'public/data/planning/maui.json').read_text(encoding='utf-8'));source=json.loads((root/'public/data/research/harmonization.json').read_text(encoding='utf-8'))
    config={'model_id':data['model_id'],'tie_break':'stable grid identifier ascending','area_fractions':[.1,.2,.3],'methods':['annual','monthly'],'holdout_disclosure':'2023 descriptive data exposed in prior development; exploratory not blinded'}
    dest=root/'data/processed/planning';dest.mkdir(parents=True,exist_ok=True);lock=dest/'evaluation_config.lock.json'
    if lock.exists() and json.loads(lock.read_text())!=config:raise ValueError('evaluation configuration changed')
    if not lock.exists():lock.write_text(json.dumps(config,sort_keys=True),encoding='utf-8')
    events={p:set() for p in ['validation','test']}
    for f in source['observations']['features']:
        p=f['properties']
        if p['partition'] in events:events[p['partition']].add((p['gridId'],datetime.fromisoformat(p['acquiredAt']).astimezone(ZoneInfo('Pacific/Honolulu')).date().isoformat()))
    grid=data['grid'];areas=[c['area_m2'] for c in grid];total=sum(areas);annual=[sum(data['monthly_weights'][str(m)][i] for m in range(1,13)) for i in range(len(grid))];out=[]
    for partition,days in events.items():
        for fraction in config['area_fractions']:
            for method in config['methods']:
                choices={};actual=[]
                for month in range(1,13):
                    weights=annual if method=='annual' else data['monthly_weights'][str(month)];order=sorted(range(len(grid)),key=lambda i:(-weights[i],grid[i]['id']));selected=set();used=0
                    for i in order:
                        if used+areas[i]<=total*fraction:selected.add(grid[i]['id']);used+=areas[i]
                    choices[month]=selected;actual.append(used/total)
                captured=sum(cell in choices[int(day[5:7])] for cell,day in days)
                out.append({'partition':partition,'method':method,'requested_area_fraction':fraction,'actual_mean_area_fraction':sum(actual)/12,'positive_cell_days':len(days),'captured_positive_cell_days':captured,'capture_fraction':captured/len(days) if days else None,'uniform_expected_capture_fraction':fraction,'notes':'Zero-score cells included only to fill equal evaluation area; not classified safe. Tie-break ordering matters.'})
    path=root/'public/data/planning/historical_validation.json';path.write_text(json.dumps({'configuration':config,'results':out},indent=2),encoding='utf-8');return out
if __name__=='__main__':print(json.dumps(evaluate(),indent=2))
