import {describe,it,expect} from 'vitest';
import {validateSpatial} from '../src/services/spatial';
describe('spatial data validation',()=>{
 it('rejects invalid coordinates and unsupported sensors',()=>expect(validateSpatial({type:'FeatureCollection',features:[{type:'Feature',geometry:{type:'Point',coordinates:[400,20]},properties:{id:'x',sensor:'other',satellite:'x',acquiredAt:'2020-01-01T00:00:00Z'}}]}).ok).toBe(false));
 it('accepts documented observations without inventing a metric',()=>expect(validateSpatial({type:'FeatureCollection',features:[{type:'Feature',geometry:{type:'Point',coordinates:[-156.3,20.8]},properties:{id:'x',sensor:'VIIRS',satellite:'Suomi NPP',acquiredAt:'2020-01-01T00:00:00Z',confidence:'n',frpMw:null}}]}).ok).toBe(true));
});
