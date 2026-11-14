import {describe,it,expect} from 'vitest';
import {monthlyResearchCounts} from '../src/services/seasonal';
describe('monthly research observations',()=>{
 it('counts only the selected UTC year and preserves missing months',()=>{
  const dates=['2023-08-01T00:00:00Z','2023-08-03T12:00:00Z','2022-07-01T00:00:00Z'];
  expect(monthlyResearchCounts(dates,'2023')[7]).toBe(2);
  expect(monthlyResearchCounts(dates,'2023')[6]).toBeNull();
  expect(monthlyResearchCounts(dates,'all')[6]).toBe(1);
 });
});
