export type Classification = 'synthetic' | 'real';
export interface Provenance { sourceOrganization: string; productName: string; sensor: string; satellite: string; processingVersion: string; acquisitionTimeRange: [string,string]; geographicExtent: [number,number,number,number]; processingDate: string; recordCount: number; units: Record<string,string>; limitations: string[]; classification: Classification }
export interface RawHotspot { longitude:number; latitude:number; acquiredAt:string; sensor:string; satellite:string; confidence:string|number; frp:number|null; provenance:Provenance }
export interface HarmonizedObservation { id:string; longitude:number; latitude:number; acquiredAt:string; sourceObservationIds:string[]; sensors:string[]; matchUncertainty:string }
export interface GridCell { id:string; geometry:GeoJSONGeometry; }
export interface GeoJSONGeometry { type:string; coordinates:unknown }
export interface SeasonalActivity { cellId:string; year:number; month:number; observations:number }
export interface FireStation { id:string; name:string; longitude:number; latitude:number; provenance:Provenance }
export interface ResourceInventory { stationId:string; count:number; classification:'verified'|'hypothetical' }
export interface CoverageAnalysis { scenarioId:string; method:'distance'|'road-network'; coverage:number; units:string; assumptions:string[] }
export interface OptimizationScenario { resources:number; month:number; coverageTarget:number; baseline:string }
export interface OptimizationResult { scenarioId:string; allocations:ResourceInventory[]; coverage:CoverageAnalysis; assumptions:string[] }
export interface ValidationReport { valid:boolean; errors:string[]; warnings:string[] }
export interface DatasetManifest { schemaVersion:'1.0'; provenance:Provenance; files:string[] }
export interface OptimizationService { run(scenario:OptimizationScenario): Promise<OptimizationResult> }
export const unavailableSolver:OptimizationService = { async run() { throw new Error('Optimization service is not implemented'); } };
export interface ModisRecord extends RawHotspot {sensor:'MODIS'; confidence:number}
export interface ViirsRecord extends RawHotspot {sensor:'VIIRS'; confidence:'low'|'nominal'|'high'}
export interface RoadNetworkCost {originId:string; destinationId:string; seconds:number; networkVersion:string; assumptions:string[]}
export interface ScientificValidationMetrics {period:[string,string]; method:string; metrics:Record<string,number>; limitations:string[]}
