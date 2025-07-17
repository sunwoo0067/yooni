export interface Product {
  id: number;
  raw_data_id?: number;
  supplier_id: number;
  product_key: string;
  name: string;
  price?: number;
  status: string;
  stock_status?: 'in_stock' | 'out_of_stock' | 'low_stock';
  stock_quantity?: number;
  last_stock_check?: Date;
  stock_sync_enabled?: boolean;
  metadata?: any;
  created_at: Date;
  updated_at: Date;
}

export interface ProductOption {
  id: string;
  name: string;
  value: string;
  price?: number;
  stock?: number;
}

export interface Supplier {
  id: number;
  name: string;
  code: string;
}

export interface StockHistory {
  id: number;
  product_id: number;
  previous_status?: string;
  new_status?: string;
  previous_quantity?: number;
  new_quantity?: number;
  change_reason: 'api_sync' | 'manual_update' | 'order_placed' | 'order_cancelled';
  created_at: Date;
}

export interface StockAlert {
  id: number;
  product_id: number;
  alert_type: 'out_of_stock' | 'low_stock' | 'back_in_stock';
  message: string;
  is_read: boolean;
  created_at: Date;
}

export const SUPPLIERS: Record<number, Supplier> = {
  1: { id: 1, name: '오너클랜', code: 'ownerclan' },
  2: { id: 2, name: '젠트레이드', code: 'zentrade' },
  3: { id: 3, name: '도매매', code: 'domemae' }
};