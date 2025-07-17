import { NextRequest, NextResponse } from 'next/server';
import { query, getOne } from '@/lib/db';

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const supplierId = parseInt(params.id);
    const body = await request.json();
    const { periodType, periodValue, startDate, endDate } = body;
    
    // 공급업체 확인
    const supplier = await getOne(
      'SELECT id, name FROM suppliers WHERE id = $1',
      [supplierId]
    );
    
    if (!supplier) {
      return NextResponse.json(
        { error: '공급업체를 찾을 수 없습니다.' },
        { status: 404 }
      );
    }
    
    // 수집 기간 계산
    let collectionStartDate = new Date();
    let collectionEndDate = new Date();
    
    if (startDate && endDate) {
      // 커스텀 기간
      collectionStartDate = new Date(startDate);
      collectionEndDate = new Date(endDate);
    } else if (periodType && periodValue) {
      // 상대적 기간
      if (periodType === 'days') {
        collectionStartDate.setDate(collectionStartDate.getDate() - periodValue);
      } else if (periodType === 'months') {
        collectionStartDate.setMonth(collectionStartDate.getMonth() - periodValue);
      }
    }
    
    // 수집 로그 생성 (metadata 컬럼이 없을 수 있으므로 우선 기본 정보만)
    const log = await getOne(
      `INSERT INTO collection_logs (supplier_id, started_at, status) 
       VALUES ($1, NOW(), 'running') 
       RETURNING id`,
      [supplierId]
    );
    
    // 백그라운드에서 수집 프로세스 실행
    // 실제 운영환경에서는 Queue 시스템이나 별도 Worker 프로세스 사용 권장
    setTimeout(async () => {
      try {
        // 동적 import로 서버 사이드에서만 실행
        const { CollectionManager } = await import('@/lib/collection/collection-manager');
        await CollectionManager.runCollection(supplierId, {
          startDate: collectionStartDate,
          endDate: collectionEndDate
        });
      } catch (error) {
        console.error('Collection process failed:', error);
        // 실패 시 로그 업데이트
        await query(
          `UPDATE collection_logs 
           SET completed_at = NOW(), status = 'failed', error_message = $1
           WHERE id = $2`,
          [String(error), log?.id]
        );
      }
    }, 0);
    
    const periodDescription = startDate && endDate 
      ? `${new Date(startDate).toLocaleDateString('ko-KR')} ~ ${new Date(endDate).toLocaleDateString('ko-KR')}`
      : periodType === 'days' 
        ? `최근 ${periodValue}일`
        : periodType === 'months'
          ? `최근 ${periodValue}개월`
          : '전체 기간';
    
    return NextResponse.json({
      message: `${supplier.name} ${periodDescription} 상품 수집을 시작했습니다.`,
      logId: log?.id
    });
  } catch (error) {
    console.error('Error starting collection:', error);
    return NextResponse.json(
      { error: '수집 시작 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}