import {evaluateCoverage} from './optimizer';
export type Assignment={vehicle:number;incident:number;distance:number};
export function assignIncidents(costs:number[][],threshold:number,incidentCount=costs[0]?.length??0){
 if(costs.length>20||incidentCount>10||!Number.isInteger(incidentCount)||incidentCount<0||threshold<0||!Number.isFinite(threshold)||costs.some(r=>r.length!==incidentCount||r.some(v=>!Number.isFinite(v)||v<0)))throw Error('Invalid incident scenario');
 const memo=new Map<string,{assignments:Assignment[];distance:number}>();
 function solve(i:number,mask:number):{assignments:Assignment[];distance:number}{if(i===incidentCount)return {assignments:[],distance:0};const key=`${i}:${mask}`;const cached=memo.get(key);if(cached)return cached;let best=solve(i+1,mask);for(let vehicle=0;vehicle<costs.length;vehicle++){const distance=costs[vehicle][i];if(mask&(1<<vehicle)||distance>threshold)continue;const rest=solve(i+1,mask|(1<<vehicle));const candidate={assignments:[{vehicle,incident:i,distance},...rest.assignments],distance:rest.distance+distance};if(candidate.assignments.length>best.assignments.length||(candidate.assignments.length===best.assignments.length&&candidate.distance<best.distance))best=candidate;}memo.set(key,best);return best;}
 const result=solve(0,0);return {...result,served:result.assignments.length,unserved:Array.from({length:incidentCount},(_,i)=>i).filter(i=>!result.assignments.some(a=>a.incident===i))};
}
export function allocationDistribution(costs:number[][],weights:number[],budget:number,threshold:number){
 if(!Number.isInteger(budget)||budget<0||budget>costs.length||costs.length>20)throw Error('invalid budget');const values:number[]=[];
 function visit(selected:number[],start:number){if(selected.length===budget){values.push(evaluateCoverage(costs,weights,selected,threshold).coveredWeight);return;}for(let i=start;i<=costs.length-(budget-selected.length);i++)visit([...selected,i],i+1);}
 visit([],0);values.sort((a,b)=>a-b);const mid=Math.floor(values.length/2);return {count:values.length,min:values[0],max:values.at(-1)!,median:values.length%2?values[mid]:(values[mid-1]+values[mid])/2};
}
