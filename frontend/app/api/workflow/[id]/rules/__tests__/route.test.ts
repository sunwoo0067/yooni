import { GET } from '../route'
import { NextRequest } from 'next/server'

// Mock the pg pool
const mockPool = {
  query: jest.fn()
}

jest.mock('pg', () => ({
  Pool: jest.fn().mockImplementation(() => mockPool)
}))

describe('/api/workflow/[id]/rules', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  it('워크플로우 규칙을 성공적으로 반환한다', async () => {
    const mockRules = [
      {
        id: 1,
        workflow_id: 1,
        rule_order: 1,
        condition_type: 'price_change',
        condition_config: { threshold: 10 },
        action_type: 'send_notification',
        action_config: { channel: 'email' }
      },
      {
        id: 2,
        workflow_id: 1,
        rule_order: 2,
        condition_type: 'stock_low',
        condition_config: { level: 5 },
        action_type: 'reorder',
        action_config: { supplier_id: 123 }
      }
    ]
    
    mockPool.query.mockResolvedValueOnce({
      rows: mockRules
    })
    
    const request = new NextRequest('http://localhost:3000/api/workflow/1/rules')
    const context = { params: Promise.resolve({ id: '1' }) }
    const response = await GET(request, context)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.rules).toHaveLength(2)
    expect(data.rules[0].rule_order).toBe(1)
    expect(data.rules[1].rule_order).toBe(2)
    
    // Verify correct query
    expect(mockPool.query).toHaveBeenCalledWith(
      expect.stringContaining('WHERE workflow_id = $1'),
      ['1']
    )
    expect(mockPool.query).toHaveBeenCalledWith(
      expect.stringContaining('ORDER BY rule_order'),
      ['1']
    )
  })
  
  it('빈 규칙 목록을 처리한다', async () => {
    mockPool.query.mockResolvedValueOnce({ rows: [] })
    
    const request = new NextRequest('http://localhost:3000/api/workflow/999/rules')
    const context = { params: Promise.resolve({ id: '999' }) }
    const response = await GET(request, context)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.rules).toHaveLength(0)
    expect(Array.isArray(data.rules)).toBe(true)
  })
  
  it('데이터베이스 오류를 처리한다', async () => {
    mockPool.query.mockRejectedValueOnce(new Error('Database connection failed'))
    
    const request = new NextRequest('http://localhost:3000/api/workflow/1/rules')
    const context = { params: Promise.resolve({ id: '1' }) }
    const response = await GET(request, context)
    const data = await response.json()
    
    expect(response.status).toBe(500)
    expect(data.error).toBe('Failed to fetch workflow rules')
  })
})