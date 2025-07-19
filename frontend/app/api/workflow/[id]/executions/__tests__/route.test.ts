import { GET } from '../route'
import { NextRequest } from 'next/server'

// Mock the pg pool
const mockPool = {
  query: jest.fn()
}

jest.mock('pg', () => ({
  Pool: jest.fn().mockImplementation(() => mockPool)
}))

describe('/api/workflow/[id]/executions', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  it('워크플로우 실행 이력을 성공적으로 반환한다', async () => {
    const mockExecutions = [
      {
        id: 1,
        workflow_id: 1,
        status: 'completed',
        started_at: new Date('2024-01-15T10:00:00Z'),
        completed_at: new Date('2024-01-15T10:00:05Z'),
        execution_time_ms: 5000,
        trigger_data: { product_id: 123 },
        result_data: { success: true, items_processed: 5 },
        error_message: null
      },
      {
        id: 2,
        workflow_id: 1,
        status: 'failed',
        started_at: new Date('2024-01-15T09:30:00Z'),
        completed_at: new Date('2024-01-15T09:30:02Z'),
        execution_time_ms: 2000,
        trigger_data: { product_id: 456 },
        result_data: null,
        error_message: 'Validation failed'
      }
    ]
    
    mockPool.query.mockResolvedValueOnce({
      rows: mockExecutions
    })
    
    const request = new NextRequest('http://localhost:3000/api/workflow/1/executions')
    const context = { params: Promise.resolve({ id: '1' }) }
    const response = await GET(request, context)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.executions).toHaveLength(2)
    expect(data.executions[0].status).toBe('completed')
    expect(data.executions[1].status).toBe('failed')
    
    // Verify correct query
    expect(mockPool.query).toHaveBeenCalledWith(
      expect.stringContaining('WHERE workflow_id = $1'),
      ['1', 20]
    )
    expect(mockPool.query).toHaveBeenCalledWith(
      expect.stringContaining('ORDER BY started_at DESC'),
      ['1', 20]
    )
  })
  
  it('limit 파라미터를 적용한다', async () => {
    mockPool.query.mockResolvedValueOnce({ rows: [] })
    
    const request = new NextRequest('http://localhost:3000/api/workflow/1/executions?limit=50')
    const context = { params: Promise.resolve({ id: '1' }) }
    const response = await GET(request, context)
    
    expect(response.status).toBe(200)
    expect(mockPool.query).toHaveBeenCalledWith(
      expect.any(String),
      ['1', '50']
    )
  })
  
  it('기본 limit 값을 사용한다', async () => {
    mockPool.query.mockResolvedValueOnce({ rows: [] })
    
    const request = new NextRequest('http://localhost:3000/api/workflow/2/executions')
    const context = { params: Promise.resolve({ id: '2' }) }
    const response = await GET(request, context)
    
    expect(response.status).toBe(200)
    expect(mockPool.query).toHaveBeenCalledWith(
      expect.any(String),
      ['2', 20] // Default limit
    )
  })
  
  it('빈 실행 이력을 처리한다', async () => {
    mockPool.query.mockResolvedValueOnce({ rows: [] })
    
    const request = new NextRequest('http://localhost:3000/api/workflow/999/executions')
    const context = { params: Promise.resolve({ id: '999' }) }
    const response = await GET(request, context)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.executions).toHaveLength(0)
    expect(Array.isArray(data.executions)).toBe(true)
  })
  
  it('데이터베이스 오류를 처리한다', async () => {
    mockPool.query.mockRejectedValueOnce(new Error('Database connection failed'))
    
    const request = new NextRequest('http://localhost:3000/api/workflow/1/executions')
    const context = { params: Promise.resolve({ id: '1' }) }
    const response = await GET(request, context)
    const data = await response.json()
    
    expect(response.status).toBe(500)
    expect(data.error).toBe('Failed to fetch workflow executions')
  })
  
  it('0 limit 값을 처리한다', async () => {
    mockPool.query.mockResolvedValueOnce({ rows: [] })
    
    const request = new NextRequest('http://localhost:3000/api/workflow/1/executions?limit=0')
    const context = { params: Promise.resolve({ id: '1' }) }
    const response = await GET(request, context)
    
    expect(response.status).toBe(200)
    expect(mockPool.query).toHaveBeenCalledWith(
      expect.any(String),
      ['1', '0']
    )
  })
})