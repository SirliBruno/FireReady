import {describe,it,expect} from 'vitest';
import {validateResearch} from '../src/services/research';
describe('research preview validation',()=>{
 it('rejects malformed and synthetic-as-real inputs',()=>{expect(validateResearch({})).toBeNull();expect(validateResearch({classification:'synthetic'})).toBeNull()});
});
import {validateResearchSummary} from '../src/services/research';
it('validates compact summary independently of map payload',()=>{expect(validateResearchSummary({})).toBeNull()});
import {validateResearchGrid} from '../src/services/research';
it('rejects malformed grid geometry',()=>{expect(validateResearchGrid({type:'FeatureCollection',features:[{type:'Feature',geometry:{type:'Polygon',coordinates:'not coordinates'},properties:{grid_cell_id:'x',area_m2:2}}]})).toBe(false)});
