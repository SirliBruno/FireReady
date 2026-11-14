import { describe, expect, it } from 'vitest';
import { parseManifest } from '../src/data.mjs';
describe('dataset classification', () => {
 it('rejects invalid inputs', () => { expect(parseManifest({})).toEqual({status:'invalid'}); expect(parseManifest(null)).toEqual({status:'invalid'}); });
 it('never treats a real manifest alone as verified', () => expect(parseManifest({classification:'real',source:'example',recordCount:1})).toEqual({status:'unverified'}));
 it('labels synthetic data separately', () => expect(parseManifest({classification:'synthetic',source:'fixture',recordCount:0})).toEqual({status:'synthetic'}));
});
