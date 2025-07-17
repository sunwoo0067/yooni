import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Order } from '@/lib/types/order';

interface OrdersResponse {
  orders: (Order & { item_count: string; total_quantity: string })[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

interface UseOrdersParams {
  page?: number;
  limit?: number;
  search?: string;
  supplier?: string;
  status?: string;
  startDate?: string;
  endDate?: string;
}

export function useOrders(params: UseOrdersParams = {}) {
  return useQuery<OrdersResponse>({
    queryKey: ['orders', params],
    queryFn: async () => {
      const { data } = await axios.get('/api/orders', { params });
      return data;
    },
  });
}