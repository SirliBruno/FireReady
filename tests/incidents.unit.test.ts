import {it,expect} from 'vitest';
import {assignIncidents,allocationDistribution} from '../src/services/incidents';
it('assigns each vehicle once and maximizes served before distance',()=>{const r=assignIncidents([[1,2],[2,100]],3);expect(r.served).toBe(2);expect(new Set(r.assignments.map(a=>a.vehicle)).size).toBe(2);expect(r.distance).toBe(4)});
it('unreachable incidents and zero vehicles remain unserved',()=>{expect(assignIncidents([[10]],1).served).toBe(0);expect(assignIncidents([],1,2).unserved).toEqual([0,1])});
it('enumerates all fixed-budget coverage alternatives',()=>{const r=allocationDistribution([[1,9],[9,1]],[1,1],1,2);expect(r.count).toBe(2);expect(r.median).toBe(1)});

it('one vehicle cannot serve two simultaneous incidents and equality is reachable',()=>{const r=assignIncidents([[2,2]],2);expect(r.served).toBe(1);expect(r.unserved).toHaveLength(1);expect(r.distance).toBe(2)});
it('rejects malformed incident dimensions',()=>{expect(()=>assignIncidents([[1],[]],2)).toThrow();expect(()=>assignIncidents([[Number.NaN]],2)).toThrow()});
