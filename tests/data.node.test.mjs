import { test } from 'node:test';
import { strict as assert } from 'node:assert';
import { parseManifest } from '../src/data.mjs';
test('rejects malformed manifests', () => assert.deepEqual(parseManifest({}), {status:'invalid'}));
test('keeps synthetic data separate from verified data', () => assert.deepEqual(parseManifest({classification:'synthetic',source:'fixture',recordCount:0}), {status:'synthetic'}));
