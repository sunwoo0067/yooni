import { BaseCollector } from './base-collector';
import { OwnerClanCollector } from './ownerclan-collector';

export class CollectionManager {
  static async createCollector(
    supplierId: number, 
    config: any
  ): Promise<BaseCollector | null> {
    switch (config.api_type?.toLowerCase()) {
      case 'graphql':
        if (config.api_endpoint?.includes('ownerclan')) {
          return new OwnerClanCollector(supplierId, config);
        }
        break;
      case 'rest':
        // ZenTrade collector 구현 예정
        console.log('REST API collector not implemented yet');
        break;
      case 'crawling':
        // 도매매 crawler 구현 예정
        console.log('Web crawler not implemented yet');
        break;
    }
    
    return null;
  }

  static async runCollection(
    supplierId: number, 
    options?: { startDate?: Date; endDate?: Date }
  ): Promise<any> {
    try {
      // 공급사 설정 가져오기
      const configResponse = await fetch(`/api/suppliers/${supplierId}/config`);
      if (!configResponse.ok) {
        throw new Error('Failed to fetch supplier config');
      }
      
      const config = await configResponse.json();
      
      // 수집기 생성
      const collector = await this.createCollector(supplierId, config);
      if (!collector) {
        throw new Error('No collector available for this supplier');
      }
      
      // 수집 실행 (기간 옵션 전달)
      const result = await collector.collect(options);
      
      // 결과 저장
      await fetch(`/api/suppliers/${supplierId}/collect/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...result,
          collection_period: options
        })
      });
      
      return result;
      
    } catch (error) {
      console.error('Collection failed:', error);
      throw error;
    }
  }
}