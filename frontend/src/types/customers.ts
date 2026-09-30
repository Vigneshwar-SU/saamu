export const GARMENT_TYPES = ['SHIRT', 'PANT'] as const;

export type GarmentType = (typeof GARMENT_TYPES)[number];

/**
 * Shirt variants. A SHIRT line is always one of these; PANT lines never have
 * one. `null` only ever occurs on historical rows created before variants
 * existed, which the UI still labels as a plain "Shirt".
 */
export const SHIRT_TYPES = ['FULL', 'HALF'] as const;

export type ShirtType = (typeof SHIRT_TYPES)[number];

export const SHIRT_TYPE_LABELS: Record<ShirtType, string> = {
  FULL: 'Full Shirt',
  HALF: 'Half Shirt',
};

export const GARMENT_TYPE_LABELS: Record<GarmentType, string> = {
  SHIRT: 'Shirt',
  PANT: 'Pant',
};

/**
 * Configurable piece-rate keys. Full and Half Shirt are priced and paid
 * separately, so each has its own rate; pants use the plain key.
 */
export const PIECE_RATE_KEYS = ['SHIRT_FULL', 'SHIRT_HALF', 'PANT'] as const;

export type PieceRateKey = (typeof PIECE_RATE_KEYS)[number];

export const PIECE_RATE_LABELS: Record<PieceRateKey, string> = {
  SHIRT_FULL: 'Full Shirt',
  SHIRT_HALF: 'Half Shirt',
  PANT: 'Pant',
};

/** Historical rate key for pre-variant shirt lines; still resolvable. */
export const LEGACY_SHIRT_RATE_KEY = 'SHIRT';

/**
 * Resolves the configurable piece-rate key an order line is paid by.
 * Mirrors the backend `piece_rate_key` helper so the UI can show the exact
 * rate the backend will snapshot, without a second guess at the mapping.
 * A historical shirt line with no recorded variant keeps the legacy `SHIRT`
 * key rather than being assumed to be a Full Shirt.
 */
export const resolvePieceRateKey = (
  garmentType: string,
  shirtType?: string | null,
): string => {
  if (garmentType === 'SHIRT') {
    if (shirtType === 'FULL') return 'SHIRT_FULL';
    if (shirtType === 'HALF') return 'SHIRT_HALF';
    return LEGACY_SHIRT_RATE_KEY;
  }
  if (garmentType === 'PANT') return 'PANT';
  return garmentType;
};

/** Display label for a stored rate key, including historical ones. */
export const formatPieceRateKey = (key: string): string =>
  (PIECE_RATE_LABELS as Record<string, string>)[key] ??
  (key === LEGACY_SHIRT_RATE_KEY ? GARMENT_TYPE_LABELS.SHIRT : key);

/**
 * Single source of truth for how a garment line is labelled everywhere.
 * Mirrors the backend `garment_label` helper so list, detail, invoice and
 * communication output can never disagree. A legacy SHIRT line with no
 * recorded variant stays "Shirt" rather than being assumed to be a Full Shirt.
 */
export const formatGarmentLabel = (
  garmentType: string,
  shirtType?: string | null,
): string => {
  if (garmentType === 'SHIRT') {
    if (shirtType === 'FULL') return SHIRT_TYPE_LABELS.FULL;
    if (shirtType === 'HALF') return SHIRT_TYPE_LABELS.HALF;
    return GARMENT_TYPE_LABELS.SHIRT;
  }
  if (garmentType === 'PANT') return GARMENT_TYPE_LABELS.PANT;
  return garmentType;
};

export type CustomerStatus = 'active' | 'archived' | 'all';

export interface Customer {
  id: number;
  full_name: string;
  mobile_number: string;
  alternate_mobile_number: string;
  address: string;
  notes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CustomerListResult {
  count: number;
  next: string | null;
  previous: string | null;
  results: Customer[];
}

export interface CustomerListParams {
  search?: string;
  status?: CustomerStatus;
  page?: number;
}

export interface CustomerPayload {
  full_name: string;
  mobile_number: string;
  alternate_mobile_number?: string;
  address?: string;
  notes?: string;
}

export interface ApiMessageResponse {
  success: boolean;
  message?: string;
}

// ---- Measurements ----

export const SHIRT_MEASUREMENT_FIELDS = [
  'neck_circumference',
  'chest_circumference',
  'waist_circumference',
  'shoulder_width',
  'sleeve_length',
  'sleeve_circumference',
  'cuff_circumference',
  'shirt_length',
  'body_loose',
  'chest_loose',
  'armfold_loose',
] as const;

export const PANT_MEASUREMENT_FIELDS = [
  'waist_circumference',
  'hip_circumference',
  'thigh_circumference',
  'knee_circumference',
  'bottom_circumference',
  'length',
  'half_length',
] as const;

export const ALL_MEASUREMENT_FIELDS = [
  ...new Set([...SHIRT_MEASUREMENT_FIELDS, ...PANT_MEASUREMENT_FIELDS]),
] as const;

export type MeasurementFieldName = (typeof ALL_MEASUREMENT_FIELDS)[number];

export const MEASUREMENT_FIELDS_BY_GARMENT: Record<GarmentType, readonly MeasurementFieldName[]> = {
  SHIRT: SHIRT_MEASUREMENT_FIELDS,
  PANT: PANT_MEASUREMENT_FIELDS,
};

export const MEASUREMENT_REQUIRED_FIELDS: Record<GarmentType, readonly MeasurementFieldName[]> = {
  SHIRT: [
    'neck_circumference',
    'chest_circumference',
    'waist_circumference',
    'shoulder_width',
    'sleeve_length',
    'shirt_length',
  ],
  PANT: ['waist_circumference', 'hip_circumference', 'length'],
};

export const MEASUREMENT_FIELD_LABELS: Record<MeasurementFieldName, string> = {
  neck_circumference: 'Neck Round',
  chest_circumference: 'Chest Round',
  waist_circumference: 'Waist Round',
  shoulder_width: 'Shoulder Width',
  sleeve_length: 'Sleeve Length',
  sleeve_circumference: 'Sleeve Round (Bicep)',
  cuff_circumference: 'Cuff Round',
  shirt_length: 'Shirt Length',
  body_loose: 'Body Loose',
  chest_loose: 'Chest Loose',
  armfold_loose: 'Armfold Loose',
  hip_circumference: 'Hip / Seat Round',
  thigh_circumference: 'Thigh Round',
  knee_circumference: 'Knee Round',
  bottom_circumference: 'Bottom Round',
  length: 'Pant Length',
  half_length: 'Half Length',
};

export interface Measurement {
  id: number;
  customer: number;
  garment_type: GarmentType;
  version: number;
  is_current: boolean;
  notes: string;
  created_at: string;
  updated_at: string;
  neck_circumference: number | null;
  chest_circumference: number | null;
  waist_circumference: number | null;
  shoulder_width: number | null;
  sleeve_length: number | null;
  sleeve_circumference: number | null;
  cuff_circumference: number | null;
  shirt_length: number | null;
  body_loose: number | null;
  chest_loose: number | null;
  armfold_loose: number | null;
  hip_circumference: number | null;
  thigh_circumference: number | null;
  knee_circumference: number | null;
  bottom_circumference: number | null;
  length: number | null;
  half_length: number | null;
}

export type MeasurementFormValues = Partial<Record<MeasurementFieldName, number | null>>;

export interface MeasurementPayload extends MeasurementFormValues {
  garment_type: GarmentType;
  notes?: string;
}
