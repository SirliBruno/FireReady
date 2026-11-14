import { describe, expect, it } from 'vitest';
import { validateBundle, fixtureBundle } from '../src/services/repository';
describe('dataset repository', () => {
 it('rejects malformed input safely', () => expect(validateBundle({})).toMatchObject({ok:false}));
 it('accepts the isolated synthetic fixture', () => expect(validateBundle(fixtureBundle)).toMatchObject({ok:true, data:{classification:'synthetic'}}));
 it('does not allow a synthetic bundle to masquerade as reviewed real data', () => expect(validateBundle({...fixtureBundle,classification:'real'})).toMatchObject({ok:false}));
 it('rejects negative counts or wrong month', () => expect(validateBundle({...fixtureBundle,observations:[{month:13,year:2020,count:-1}]})).toMatchObject({ok:false}));
});
