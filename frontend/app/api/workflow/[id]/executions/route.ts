import { NextRequest, NextResponse } from 'next/server'
import { Pool } from 'pg'

const pool = new Pool({
  host: 'localhost',
  port: 5434,
  database: 'yoonni',
  user: 'postgres',
  password: '1234'
})

// GET - 워크플로우 실행 이력 조회
export async function GET(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const params = await context.params;
    const workflowId = params.id
    const searchParams = request.nextUrl.searchParams
    const limit = searchParams.get('limit') || 20

    const result = await pool.query(`
      SELECT * FROM workflow_executions
      WHERE workflow_id = $1
      ORDER BY started_at DESC
      LIMIT $2
    `, [workflowId, limit])

    return NextResponse.json({
      executions: result.rows
    })

  } catch (error) {
    console.error('Failed to fetch workflow executions:', error)
    return NextResponse.json(
      { error: 'Failed to fetch workflow executions' },
      { status: 500 }
    )
  }
}