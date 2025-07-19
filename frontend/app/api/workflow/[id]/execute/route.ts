import { NextRequest, NextResponse } from 'next/server'

// POST - 워크플로우 실행
export async function POST(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const params = await context.params;
    const workflowId = params.id
    const body = await request.json()
    const { trigger_data } = body

    // Python 워크플로우 엔진 호출
    const response = await fetch('http://localhost:8001/execute-workflow', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workflow_id: parseInt(workflowId),
        trigger_data: trigger_data || {}
      })
    })

    if (!response.ok) {
      throw new Error('Failed to execute workflow')
    }

    const result = await response.json()
    return NextResponse.json(result)

  } catch (error) {
    console.error('Failed to execute workflow:', error)
    return NextResponse.json(
      { 
        success: false,
        error: error instanceof Error ? error.message : 'Failed to execute workflow' 
      },
      { status: 500 }
    )
  }
}