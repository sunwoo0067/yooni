import { NextRequest, NextResponse } from 'next/server'
import { Pool } from 'pg'

const pool = new Pool({
  host: 'localhost',
  port: 5434,
  database: 'yoonni',
  user: 'postgres',
  password: '1234'
})

// GET - 워크플로우 목록 조회
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const triggerType = searchParams.get('trigger_type')
    const isActive = searchParams.get('is_active')

    let query = `
      SELECT 
        wd.*,
        COUNT(we.id) as execution_count,
        MAX(we.started_at) as last_executed_at,
        AVG(we.execution_time_ms) as avg_execution_time
      FROM workflow_definitions wd
      LEFT JOIN workflow_executions we ON wd.id = we.workflow_id
      WHERE 1=1
    `
    
    const params: any[] = []
    let paramIndex = 1

    if (triggerType) {
      query += ` AND wd.trigger_type = $${paramIndex}`
      params.push(triggerType)
      paramIndex++
    }

    if (isActive !== null) {
      query += ` AND wd.is_active = $${paramIndex}`
      params.push(isActive === 'true')
      paramIndex++
    }

    query += `
      GROUP BY wd.id
      ORDER BY wd.created_at DESC
    `

    const result = await pool.query(query, params)

    return NextResponse.json({
      workflows: result.rows,
      total: result.rowCount
    })

  } catch (error) {
    console.error('Failed to fetch workflows:', error)
    return NextResponse.json(
      { error: 'Failed to fetch workflows' },
      { status: 500 }
    )
  }
}

// POST - 새 워크플로우 생성
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { name, description, trigger_type, config, rules } = body

    const client = await pool.connect()
    
    try {
      await client.query('BEGIN')

      // 워크플로우 생성
      const workflowResult = await client.query(`
        INSERT INTO workflow_definitions (name, description, trigger_type, config)
        VALUES ($1, $2, $3, $4)
        RETURNING id
      `, [name, description, trigger_type, config])

      const workflowId = workflowResult.rows[0].id

      // 규칙 생성
      for (let i = 0; i < rules.length; i++) {
        const rule = rules[i]
        await client.query(`
          INSERT INTO workflow_rules 
          (workflow_id, rule_order, condition_type, condition_config, action_type, action_config)
          VALUES ($1, $2, $3, $4, $5, $6)
        `, [
          workflowId,
          i + 1,
          rule.condition_type,
          rule.condition_config,
          rule.action_type,
          rule.action_config
        ])
      }

      // 이벤트 트리거 등록 (이벤트 기반인 경우)
      if (trigger_type === 'event' && config.event_type && config.event_source) {
        await client.query(`
          INSERT INTO event_triggers (event_type, event_source, workflow_id, filter_config)
          VALUES ($1, $2, $3, $4)
        `, [
          config.event_type,
          config.event_source,
          workflowId,
          config.filter || null
        ])
      }

      await client.query('COMMIT')

      return NextResponse.json({
        success: true,
        workflow_id: workflowId,
        message: '워크플로우가 생성되었습니다'
      })

    } catch (error) {
      await client.query('ROLLBACK')
      throw error
    } finally {
      client.release()
    }

  } catch (error) {
    console.error('Failed to create workflow:', error)
    return NextResponse.json(
      { error: 'Failed to create workflow' },
      { status: 500 }
    )
  }
}

// PUT - 워크플로우 수정
export async function PUT(request: NextRequest) {
  try {
    const body = await request.json()
    const { id, is_active } = body

    if (is_active !== undefined) {
      // 활성/비활성 토글
      await pool.query(`
        UPDATE workflow_definitions
        SET is_active = $1, updated_at = NOW()
        WHERE id = $2
      `, [is_active, id])

      return NextResponse.json({
        success: true,
        message: `워크플로우가 ${is_active ? '활성화' : '비활성화'}되었습니다`
      })
    }

    return NextResponse.json(
      { error: 'Invalid update request' },
      { status: 400 }
    )

  } catch (error) {
    console.error('Failed to update workflow:', error)
    return NextResponse.json(
      { error: 'Failed to update workflow' },
      { status: 500 }
    )
  }
}