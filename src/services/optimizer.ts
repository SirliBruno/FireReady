export type CoverageResult={selected:number[];coveredWeight:number;totalWeight:number;weightedDistance:number|null;status:'optimal'|'evaluated';};
export function evaluateCoverage(costs:number[][],weights:number[],selected:number[],threshold:number):CoverageResult{
 const totalWeight=weights.reduce((a,b)=>a+b,0);let coveredWeight=0,sum=0;
 for(let i=0;i<weights.length;i++){const distance=Math.min(...selected.map(s=>costs[s][i]));if(distance<=threshold)coveredWeight+=weights[i];sum+=Number.isFinite(distance)?distance*weights[i]:0;}
 return {selected,coveredWeight,totalWeight,weightedDistance:selected.length&&totalWeight?sum/totalWeight:null,status:'evaluated'};
}
export function optimizeCoverage(costs:number[][],weights:number[],budget:number,threshold:number):CoverageResult{
 if(!Number.isInteger(budget)||budget<0||budget>costs.length||costs.length>20||threshold<0||!Number.isFinite(threshold)||weights.some(w=>w<0||!Number.isFinite(w))||costs.some(row=>row.length!==weights.length||row.some(v=>v<0||!Number.isFinite(v))))throw Error('Invalid or infeasible scenario');
 let best:CoverageResult|null=null;
 function visit(selected:number[],start:number){if(selected.length===budget){const result=evaluateCoverage(costs,weights,selected,threshold);if(!best||result.coveredWeight>best.coveredWeight||(result.coveredWeight===best.coveredWeight&&(result.weightedDistance??Infinity)<(best.weightedDistance??Infinity)))best=result;return;}for(let i=start;i<=costs.length-(budget-selected.length);i++)visit([...selected,i],i+1);}
 visit([],0);return {...best!,status:'optimal'};
}
