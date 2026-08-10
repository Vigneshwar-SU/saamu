export interface ShopDetails {
  id: number;
  name: string;
  tagline: string;
  address: string;
  phone: string;
  established_year: number;
}

export interface ShopDetailsPayload {
  name: string;
  tagline: string;
  address: string;
  phone: string;
  established_year: number;
}
