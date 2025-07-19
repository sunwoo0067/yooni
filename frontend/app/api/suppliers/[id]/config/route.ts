import { NextRequest, NextResponse } from 'next/server';
import { getOne, query } from '@/lib/db';

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const params = await context.params;
    const { id } = await params;
    const supplierId = parseInt(id);
    
    const config = await getOne(
      `SELECT * FROM supplier_configs WHERE supplier_id = $1`,
      [supplierId]
    );
    
    if (!config) {
      return NextResponse.json(
        { error: '공급사 설정을 찾을 수 없습니다.' },
        { status: 404 }
      );
    }
    
    // 화면에서 사용하는 형식으로 변환
    return NextResponse.json({
      api_type: config.api_type,
      endpoint: config.api_endpoint,
      schedule: config.collection_schedule,
      schedule_time: config.schedule_time,
      enabled: config.collection_enabled,
      api_key: config.api_key,
      api_secret: config.api_secret,
      settings: config.settings
    });
  } catch (error) {
    console.error('Error fetching supplier config:', error);
    return NextResponse.json(
      { error: '설정 조회 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const params = await context.params;
    const { id } = await params;
    const supplierId = parseInt(id);
    const {
      api_type,
      api_endpoint,
      api_key,
      api_secret,
      collection_enabled,
      collection_schedule,
      schedule_time
    } = await request.json();
    
    // 기존 설정 확인
    const existing = await getOne(
      'SELECT id FROM supplier_configs WHERE supplier_id = $1',
      [supplierId]
    );
    
    if (existing) {
      // 기존 설정 업데이트
      await query(
        `UPDATE supplier_configs 
         SET api_type = $1, api_endpoint = $2, api_key = $3, api_secret = $4,
             collection_enabled = $5, collection_schedule = $6, schedule_time = $7,
             updated_at = NOW()
         WHERE supplier_id = $8`,
        [
          api_type,
          api_endpoint,
          api_key || '',
          api_secret || '',
          collection_enabled,
          collection_schedule,
          schedule_time || '02:00:00',
          supplierId
        ]
      );
    } else {
      // 새 설정 생성
      await query(
        `INSERT INTO supplier_configs 
         (supplier_id, api_type, api_endpoint, api_key, api_secret,
          collection_enabled, collection_schedule, schedule_time)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
        [
          supplierId,
          api_type,
          api_endpoint,
          api_key || '',
          api_secret || '',
          collection_enabled,
          collection_schedule,
          schedule_time || '02:00:00'
        ]
      );
    }
    
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error creating/updating supplier config:', error);
    return NextResponse.json(
      { error: 'Failed to save supplier config' },
      { status: 500 }
    );
  }
}