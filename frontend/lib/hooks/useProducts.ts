import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Product } from '@/lib/types/product';

interface ProductsResponse {
  products: Product[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

interface UseProductsParams {
  page?: number;
  limit?: number;
  search?: string;
  supplier?: string;
  status?: string;
  sortBy?: string;
  sortOrder?: string;
}

export function useProducts(params: UseProductsParams = {}) {
  return useQuery<ProductsResponse>({
    queryKey: ['products', params],
    queryFn: async () => {
      const { data } = await axios.get('/api/products', { params });
      return data;
    },
  });
}