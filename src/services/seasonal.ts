export function monthlyResearchCounts(dates:string[],year:string):Array<number|null>{
 const counts:Array<number|null>=Array(12).fill(null);
 for(const date of dates){if(year!=='all'&&date.slice(0,4)!==year)continue;const month=Number(date.slice(5,7));if(month>=1&&month<=12)counts[month-1]=(counts[month-1]??0)+1;}
 return counts;
}
