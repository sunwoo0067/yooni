import { BaseCollector, CollectionResult } from './base-collector';

export class OwnerClanCollector extends BaseCollector {
  private getStockStatus(quantity?: number): 'in_stock' | 'out_of_stock' | 'low_stock' {
    if (!quantity || quantity === 0) return 'out_of_stock';
    if (quantity < 10) return 'low_stock'; // 드랍쉬핑의 경우 10개 미만은 저재고로 간주
    return 'in_stock';
  }

  async collect(options?: { startDate?: Date; endDate?: Date }): Promise<CollectionResult> {
    const result: CollectionResult = {
      success: false,
      totalProducts: 0,
      newProducts: 0,
      updatedProducts: 0,
      failedProducts: 0,
      errors: []
    };

    try {
      // GraphQL 쿼리로 상품 목록 가져오기
      const query = `
        query GetItems($page: Int!, $perPage: Int!) {
          items(page: $page, perPage: $perPage) {
            data {
              id
              name
              price
              status
              stockQuantity
              category {
                id
                name
              }
              options {
                id
                name
                values
              }
              createdAt
              updatedAt
            }
            pagination {
              page
              perPage
              total
              totalPages
            }
          }
        }
      `;

      let page = 1;
      let hasMore = true;
      
      while (hasMore) {
        try {
          const response = await fetch(this.config.api_endpoint, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${this.config.api_key}`
            },
            body: JSON.stringify({
              query,
              variables: { page, perPage: 100 }
            })
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const data = await response.json();
          
          if (data.errors) {
            result.errors.push(...data.errors.map((e: any) => e.message));
            break;
          }

          const items = data.data?.items?.data || [];
          const pagination = data.data?.items?.pagination;
          
          for (const item of items) {
            result.totalProducts++;
            
            const productData = {
              product_key: item.id.toString(),
              name: item.name,
              price: item.price,
              status: item.status.toLowerCase() === 'active' ? 'active' : 'inactive',
              stock_quantity: item.stockQuantity || 0,
              stock_status: this.getStockStatus(item.stockQuantity),
              metadata: {
                stockQuantity: item.stockQuantity,
                category: item.category,
                options: item.options,
                original_data: item
              }
            };

            const saved = await this.saveProduct(productData);
            if (saved) {
              result.newProducts++; // 실제로는 new/update 구분 필요
            } else {
              result.failedProducts++;
            }
          }

          hasMore = pagination && page < pagination.totalPages;
          page++;
          
          // Rate limiting (1초에 1000 요청 제한 고려)
          await new Promise(resolve => setTimeout(resolve, 100));
          
        } catch (error) {
          result.errors.push(`페이지 ${page} 수집 실패: ${error}`);
          result.failedProducts++;
        }
      }

      result.success = result.failedProducts === 0;
      
    } catch (error) {
      result.errors.push(`수집 프로세스 오류: ${error}`);
    }

    return result;
  }
}