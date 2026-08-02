export const GARMENT_TYPES = ['SHIRT', 'PANT'] as const;

export type GarmentType = (typeof GARMENT_TYPES)[number];

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
] as const;

export const PANT_MEASUREMENT_FIELDS = [
  'waist_circumference',
  'hip_circumference',
  'thigh_circumference',
  'knee_circumference',
  'bottom_circumference',
  'length',
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
  hip_circumference: 'Hip / Seat Round',
  thigh_circumference: 'Thigh Round',
  knee_circumference: 'Knee Round',
  bottom_circumference: 'Bottom Round',
  length: 'Pant Length',
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
  hip_circumference: number | null;
  thigh_circumference: number | null;
  knee_circumference: number | null;
  bottom_circumference: number | null;
  length: number | null;
}

export type MeasurementFormValues = Partial<Record<MeasurementFieldName, number | null>>;

export interface MeasurementPayload extends MeasurementFormValues {
  garment_type: GarmentType;
  notes?: string;
}
