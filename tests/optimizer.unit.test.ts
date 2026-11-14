import {it,expect} from 'vitest';
import {optimizeCoverage,evaluateCoverage} from '../src/services/optimizer';
it('finds exact maximum coverage and respects budget',()=>{const r=optimizeCoverage([[1,10],[8,1],[1,1]],[2,3],1,2);expect(r.selected).toEqual([2]);expect(r.coveredWeight).toBe(5);});
it('zero budget and no demand are explicit',()=>{expect(optimizeCoverage([[1]],[1],0,2).selected).toEqual([]);expect(optimizeCoverage([[1]],[0],1,2).coveredWeight).toBe(0)});
it('rejects infeasible and malformed scenarios',()=>{expect(()=>optimizeCoverage([[1]],[1],2,2)).toThrow();expect(()=>optimizeCoverage([[1]],[-1],1,2)).toThrow()});
it('distinguishes evaluated references from optimized solver results',()=>{expect(evaluateCoverage([[1]],[1],[0],2).status).toBe('evaluated');expect(optimizeCoverage([[1]],[1],1,2).status).toBe('optimal')});

