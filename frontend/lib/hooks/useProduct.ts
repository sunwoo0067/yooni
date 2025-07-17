import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Product } from '@/lib/types/product';

export function useProduct(id: string) {
  return useQuery<Product>({
    queryKey: ['product', id],
    queryFn: async () => {
      const { data } = await axios.get(`/api/products/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useUpdateProduct(id: string) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (updateData: Partial<Product>) => {
      const { data } = await axios.put(`/api/products/${id}`, updateData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['product', id] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });
}