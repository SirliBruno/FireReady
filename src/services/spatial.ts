import {z} from 'zod';
const point=z.object({type:z.literal('Feature'),geometry:z.object({type:z.literal('Point'),coordinates:z.tuple([z.number().min(-180).max(180),z.number().min(-90).max(90)])}),properties:z.object({id:z.string().min(1),sensor:z.enum(['MODIS','VIIRS']),satellite:z.string().min(1),acquiredAt:z.string().datetime({offset:true}),confidence:z.string().nullable().optional(),frpMw:z.number().nonnegative().nullable().optional()})});
const collection=z.object({type:z.literal('FeatureCollection'),features:z.array(point)});
export type SpatialData=z.infer<typeof collection>;
export function validateSpatial(input:unknown):{ok:true;data:SpatialData}|{ok:false;error:string}{const result=collection.safeParse(input);return result.success?{ok:true,data:result.data}:{ok:false,error:'Invalid observation GeoJSON'};}
export async function loadSpatial():Promise<SpatialData|null>{try{const response=await fetch(`${import.meta.env.BASE_URL}data/observations.geojson`);if(!response.ok)return null;const result=validateSpatial(await response.json());return result.ok?result.data:null;}catch{return null;}}
