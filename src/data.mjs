export function parseManifest(value) {
  if (!value || typeof value !== 'object' || typeof value.source !== 'string' || !value.source.trim() || !Number.isSafeInteger(value.recordCount) || value.recordCount < 0 || !['synthetic','real'].includes(value.classification)) return {status:'invalid'};
  // A manifest alone cannot establish that a real dataset has been verified.
  return {status: value.classification === 'synthetic' ? 'synthetic' : 'unverified'};
}
