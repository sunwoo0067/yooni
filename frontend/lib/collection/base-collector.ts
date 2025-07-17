export interface CollectionResult {
  success: boolean;
  totalProducts: number;
  newProducts: number;
  updatedProducts: number;
  failedProducts: number;
  errors: string[];
}

export abstract class BaseCollector {
  protected supplierId: number;
  protected config: any;

  constructor(supplierId: number, config: any) {
    this.supplierId = supplierId;
    this.config = config;
  }

  abstract collect(options?: { startDate?: Date; endDate?: Date }): Promise<CollectionResult>;

  protected async saveProduct(productData: any): Promise<boolean> {
    try {
      const response = await fetch('/api/products/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          supplierId: this.supplierId,
          productData
        })
      });
      return response.ok;
    } catch (error) {
      console.error('Failed to save product:', error);
      return false;
    }
  }
}