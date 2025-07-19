export interface Supplier {
  id: number;
  name: string;
  created_at: Date;
  updated_at: Date;
}

export interface SupplierConfig {
  id: number;
  supplier_id: number;
  api_endpoint?: string;
  api_key?: string;
  api_secret?: string;
  collection_enabled: boolean;
  collection_schedule?: string;
  last_collected_at?: Date;
  settings?: Record<string, unknown>;
}

export interface CollectionLog {
  id: number;
  supplier_id: number;
  started_at: Date;
  completed_at?: Date;
  status: 'running' | 'completed' | 'failed';
  total_products?: number;
  new_products?: number;
  updated_products?: number;
  failed_products?: number;
  error_message?: string;
}

export interface CollectionSchedule {
  id: number;
  supplier_id: number;
  schedule_type: 'manual' | 'daily' | 'hourly' | 'realtime';
  hour?: number;
  minute?: number;
  enabled: boolean;
  last_run?: Date;
  next_run?: Date;
}