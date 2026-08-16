export interface ShopDetails {
  id: number;
  name: string;
  tagline: string;
  address: string;
  phone: string;
  established_year: number;
  customer_follow_up_months: number;
}

export interface ShopDetailsPayload {
  name: string;
  tagline: string;
  address: string;
  phone: string;
  established_year: number;
  customer_follow_up_months: number;
}
