import {useEffect,useMemo,useState} from 'react';
import {BarChart,Bar,CartesianGrid,ResponsiveContainer,Tooltip,XAxis,YAxis} from 'recharts';
import {useData} from './DataContext';
import {loadResearch,type ResearchData} from '../services/research';
import {monthlyResearchCounts} from '../services/seasonal';
export function SeasonalData(){
 const {data,mode}=useData();const [research,setResearch]=useState<ResearchData|null>(null);const [selected,setSelected]=useState('all');
 useEffect(()=>{let active=true;if(mode==='synthetic'||data){setResearch(null);return;}void loadResearch().then(value=>{if(active)setResearch(value)});return()=>{active=false}},[mode,data]);
 const dates=useMemo(()=>research?.observations.features.map(f=>f.properties.acquiredAt)??[],[research]);
 const years=useMemo(()=>[...new Set(data?data.observations.map(x=>String(x.year)):dates.map(x=>x.slice(0,4)))].sort(),[data,dates]);
 const counts=useMemo(()=>data?Array.from({length:12},(_,i)=>{const rows=data.observations.filter(x=>(selected==='all'||String(x.year)===selected)&&x.month===i+1);return rows.length?rows.reduce((n,x)=>n+x.count,0):null}):monthlyResearchCounts(dates,selected),[data,dates,selected]);
 const points=counts.map((count,i)=>({month:new Date(2020,i,1).toLocaleString('ar',{month:'short'}),count}));
 if(!data&&!research)return <div className="chart-empty"><strong>بانتظار المشاهدات التاريخية</strong><p>تظهر الأنماط الشهرية عند توفر البيانات.</p></div>;
 return <div className="chart-content">{mode==='synthetic'&&<strong className="synthetic-label">بيانات تجريبية مصطنعة لاختبار الواجهة</strong>}{research&&<p className="research-warning">مشاهدات بحثية مقدمة من المستخدم؛ لم يُتحقق من مصدرها مستقلاً. المجموعة المرجعية تستبعد NOAA-20.</p>}<div className="chart-controls"><label>السنة <select value={selected} onChange={e=>setSelected(e.target.value)}><option value="all">كل السنوات المتاحة</option>{years.map(y=><option value={y} key={y}>{y}</option>)}</select></label><span>الوحدة: عدد المشاهدات</span></div><div className="chart-frame"><ResponsiveContainer width="100%" height="100%"><BarChart data={points} margin={{top:15,right:10,left:-20,bottom:0}}><CartesianGrid stroke="#34414a" vertical={false}/><XAxis dataKey="month" stroke="#a9bbc1" fontSize={10}/><YAxis allowDecimals={false} stroke="#a9bbc1" fontSize={10}/><Tooltip contentStyle={{background:'#17232b',border:'1px solid #40525a'}}/><Bar isAnimationActive={false} dataKey="count" fill="#ed8d50" name="المشاهدات"/></BarChart></ResponsiveContainer></div><p className="caption">{research?'يعرض الرسم مشاهدات MODIS وSuomi NPP في ماوي حسب شهر الرصد بتوقيت UTC. قد يرصد المستشعران الحدث نفسه.':'الأعداد مجمّعة من السجلات الشهرية.'} غياب عمود لا يثبت عدم وجود نشاط؛ تتأثر المشاهدات بتغطية الأقمار والسحب. هذه الأعداد ليست حوادث منفردة أو توقعاً للحرائق.</p></div>;
}
