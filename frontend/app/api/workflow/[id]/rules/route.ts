import { NextRequest, NextResponse } from 'next/server'
import { Pool } from 'pg'

const pool = new Pool({
  host: 'localhost',
  port: 5434,
  database: 'yoonni',
  user: 'postgres',
  password: '1234'
})

// GET - 워크플로우 규칙 조회
export async function GET(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const params = await context.params;
    const workflowId = params.id

    const result = await pool.query(`
      SELECT * FROM workflow_rules
      WHERE workflow_id = $1
      ORDER BY rule_order
    `, [workflowId])

    return NextResponse.json({
      rules: result.rows
    })

  } catch (error) {
    console.error('Failed to fetch workflow rules:', error)
    return NextResponse.json(
      { error: 'Failed to fetch workflow rules' },
      { status: 500 }
    )
  }
}