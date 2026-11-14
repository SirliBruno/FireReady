import {useEffect,useState} from 'react';
import {useData} from './DataContext';
import {loadResearchSummary,type ResearchSummary} from '../services/research';
export function DatasetControl(){
 const {mode,data,message,useFixture,useReal}=useData();const [research,setResearch]=useState<ResearchSummary|null>(null);
 useEffect(()=>{let active=true;if(mode==='synthetic'){setResearch(null);return;}void loadResearchSummary().then(value=>{if(active)setResearch(value)});return()=>{active=false}},[mode]);
 return <section className="dataset-control" aria-label="مصدر البيانات"><div>{research&&mode==='awaiting'?<><b>البيانات البحثية محمّلة</b><p>{research.report.selected_reference_count} مشاهدة من MODIS وSuomi NPP داخل ماوي (2013–2023). كل نقطة رصد حراري، وليست بالضرورة حريقاً منفرداً.</p><p>استُبعد NOAA-20 من هذه الخريطة لعدم حسم نوع معالجته. مصدر الملفات لم يُتحقق منه مستقلاً.</p><a href="#harmonization">شاهد المشاهدات على الخريطة</a></>:<><b>{mode==='synthetic'?'بيانات تجريبية':mode==='real'?'بيانات مجمّعة مراجَعة':'البيانات البحثية غير متاحة'}</b><p>{mode==='awaiting'?'تعذر تحميل المعاينة البحثية. تحقق من ملفات البيانات والاتصال.':message}</p>{data&&<p>{data.provenance.sourceOrganization} · {data.provenance.productName} · {data.provenance.processingVersion}</p>}</>}</div><details><summary>تغيير مصدر العرض</summary><div className="data-buttons"><button onClick={useReal}>عرض البيانات المقدمة</button><button onClick={useFixture}>عرض بيانات تجريبية</button></div></details></section>
}
