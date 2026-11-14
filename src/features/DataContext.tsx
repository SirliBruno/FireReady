import {createContext, useContext, useEffect, useRef, useState, type ReactNode} from 'react';
import {fixtureBundle, loadReviewedData, validateBundle, type DataBundle} from '../services/repository';
type DataState={mode:'awaiting'|'synthetic'|'real';data:DataBundle|null;message:string; useFixture:()=>void; useReal:()=>void};
const Context=createContext<DataState|null>(null);
export function DataProvider({children}:{children:ReactNode}) {const [mode,setMode]=useState<DataState['mode']>('awaiting'); const [data,setData]=useState<DataBundle|null>(null);const [message,setMessage]=useState('لا تتوفر بيانات مجمّعة معتمدة للمراجعة.'); const request=useRef(0);
 const useReal=()=>{const id=++request.current;setData(null);setMode('awaiting');setMessage('جارٍ البحث عن البيانات…');void loadReviewedData().then(result=>{if(id!==request.current)return;if(result.ok){setData(result.data);setMode('real');setMessage('تم تحميل بيانات مجمّعة؛ حالة المراجعة تصريح من مشغّل البيانات.')}else setMessage("لا تتوفر بيانات مجمّعة صالحة حالياً.")})};
 useEffect(()=>{useReal()},[]);
 const useFixture=()=>{request.current++;const result=validateBundle(fixtureBundle);if(result.ok){setData(result.data);setMode('synthetic');setMessage('قيم تجريبية لتطوير الواجهة فقط.')}else{setData(null);setMode('awaiting');setMessage("تعذر تحميل البيانات التجريبية.")}};
 return <Context.Provider value={{mode,data,message,useFixture,useReal}}>{children}</Context.Provider>;
}
export function useData(){const value=useContext(Context);if(!value)throw new Error('Data provider missing');return value}

