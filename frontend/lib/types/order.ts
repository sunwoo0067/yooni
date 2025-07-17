export interface Order {
  id: number;
  order_number: string;
  supplier_id: number;
  status: 'pending' | 'confirmed' | 'processing' | 'shipped' | 'delivered' | 'cancelled' | 'returned';
  total_amount: number;
  shipping_fee: number;
  customer_name: string;
  customer_phone: string;
  customer_email?: string;
  shipping_address: string;
  shipping_postcode: string;
  order_items: OrderItem[];
  created_at: Date;
  updated_at: Date;
}

export interface OrderItem {
  id: number;
  order_id: number;
  product_id: number;
  product_name: string;
  supplier_product_id: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  options?: string;
}

export const ORDER_STATUS = {
  pending: { label: '주문대기', color: 'bg-yellow-100 text-yellow-800' },
  confirmed: { label: '주문확인', color: 'bg-blue-100 text-blue-800' },
  processing: { label: '처리중', color: 'bg-indigo-100 text-indigo-800' },
  shipped: { label: '배송중', color: 'bg-purple-100 text-purple-800' },
  delivered: { label: '배송완료', color: 'bg-green-100 text-green-800' },
  cancelled: { label: '주문취소', color: 'bg-red-100 text-red-800' },
  returned: { label: '반품', color: 'bg-gray-100 text-gray-800' },
};