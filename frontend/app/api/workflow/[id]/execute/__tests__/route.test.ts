import { POST } from '../route'
import { NextRequest } from 'next/server'

// Mock global fetch
global.fetch = jest.fn()

describe('/api/workflow/[id]/execute', () => {
  const mockFetch = fetch as jest.MockedFunction<typeof fetch>
  
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  it('워크플로우 실행을 성공적으로 처리한다', async () => {
    const mockResult = {
      success: true,
      execution_id: 'exec_123',
      workflow_id: 1,
      status: 'completed',
      duration_ms: 1500
    }
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResult)
    } as any)
    
    const request = new NextRequest('http://localhost:3000/api/workflow/1/execute', {
      method: 'POST',
      body: JSON.stringify({
        trigger_data: { product_id: 123, action: 'price_update' }
      })
    })
    
    const context = { params: Promise.resolve({ id: '1' }) }
    const response = await POST(request, context)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data).toEqual(mockResult)
    
    // Verify correct API call
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8001/execute-workflow',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_id: 1,
          trigger_data: { product_id: 123, action: 'price_update' }
        })
      }
    )
  })
  
  it('빈 트리거 데이터로 워크플로우를 실행한다', async () => {
    const mockResult = {
      success: true,
      execution_id: 'exec_456',
      workflow_id: 2
    }
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResult)
    } as any)
    
    const request = new NextRequest('http://localhost:3000/api/workflow/2/execute', {
      method: 'POST',
      body: JSON.stringify({})
    })
    
    const context = { params: Promise.resolve({ id: '2' }) }
    const response = await POST(request, context)
    
    expect(response.status).toBe(200)
    
    // Verify empty trigger_data defaults to {}
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8001/execute-workflow',
      expect.objectContaining({
        body: JSON.stringify({
          workflow_id: 2,
          trigger_data: {}
        })
      })
    )
  })
  
  it('트리거 데이터 없는 요청을 처리한다', async () => {
    const mockResult = {
      success: true,
      execution_id: 'exec_789'
    }
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResult)
    } as any)
    
    const request = new NextRequest('http://localhost:3000/api/workflow/3/execute', {
      method: 'POST',
      body: JSON.stringify({
        other_field: 'ignored'
      })
    })
    
    const context = { params: Promise.resolve({ id: '3' }) }
    const response = await POST(request, context)
    
    expect(response.status).toBe(200)
    
    // Verify undefined trigger_data defaults to {}
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        body: JSON.stringify({
          workflow_id: 3,
          trigger_data: {}
        })
      })
    )
  })
  
  it('복잡한 트리거 데이터를 처리한다', async () => {
    const complexTriggerData = {
      order: {
        id: 12345,
        customer: 'test@example.com',
        items: [
          { product_id: 1, quantity: 2, price: 29.99 },
          { product_id: 2, quantity: 1, price: 15.50 }
        ],
        total: 75.48
      },
      metadata: {
        source: 'web',
        timestamp: '2024-01-15T10:30:00Z',
        ip_address: '192.168.1.1'
      },
      flags: ['rush_order', 'new_customer']
    }
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue({ success: true })
    } as any)
    
    const request = new NextRequest('http://localhost:3000/api/workflow/5/execute', {
      method: 'POST',
      body: JSON.stringify({
        trigger_data: complexTriggerData
      })
    })
    
    const context = { params: Promise.resolve({ id: '5' }) }
    const response = await POST(request, context)
    
    expect(response.status).toBe(200)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        body: JSON.stringify({
          workflow_id: 5,
          trigger_data: complexTriggerData
        })
      })
    )
  })
  
  it('워크플로우 ID를 정수로 변환한다', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue({ success: true })
    } as any)
    
    const request = new NextRequest('http://localhost:3000/api/workflow/999/execute', {
      method: 'POST',
      body: JSON.stringify({})
    })
    
    const context = { params: Promise.resolve({ id: '999' }) }
    const response = await POST(request, context)
    
    expect(response.status).toBe(200)
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        body: JSON.stringify({
          workflow_id: 999, // Should be integer, not string
          trigger_data: {}
        })
      })
    )
  })
  
  it('워크플로우 엔진 HTTP 오류를 처리한다', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found'
    } as any)
    
    const request = new NextRequest('http://localhost:3000/api/workflow/1/execute', {
      method: 'POST',
      body: JSON.stringify({})
    })
    
    const context = { params: Promise.resolve({ id: '1' }) }
    const response = await POST(request, context)
    const data = await response.json()
    
    expect(response.status).toBe(500)
    expect(data.success).toBe(false)
    expect(data.error).toBe('Failed to execute workflow')
  })
  
  it('워크플로우 엔진 연결 오류를 처리한다', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Connection refused'))
    
    const request = new NextRequest('http://localhost:3000/api/workflow/1/execute', {
      method: 'POST',
      body: JSON.stringify({})
    })
    
    const context = { params: Promise.resolve({ id: '1' }) }
    const response = await POST(request, context)
    const data = await response.json()
    
    expect(response.status).toBe(500)
    expect(data.success).toBe(false)
    expect(data.error).toBe('Connection refused')
  })
  
  it('네트워크 타임아웃을 처리한다', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Request timeout'))
    
    const request = new NextRequest('http://localhost:3000/api/workflow/1/execute', {
      method: 'POST',
      body: JSON.stringify({})
    })
    
    const context = { params: Promise.resolve({ id: '1' }) }
    const response = await POST(request, context)
    const data = await response.json()
    
    expect(response.status).toBe(500)
    expect(data.success).toBe(false)
    expect(data.error).toBe('Request timeout')
  })
  
  it('잘못된 JSON 요청을 처리한다', async () => {
    const request = new NextRequest('http://localhost:3000/api/workflow/1/execute', {
      method: 'POST',
      body: 'invalid json'
    })
    
    const context = { params: Promise.resolve({ id: '1' }) }
    const response = await POST(request, context)
    const data = await response.json()
    
    expect(response.status).toBe(500)
    expect(data.success).toBe(false)
    expect(data.error).toBe('Failed to execute workflow')
  })
  
  it('워크플로우 엔진 JSON 파싱 오류를 처리한다', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockRejectedValue(new Error('Invalid JSON response'))
    } as any)
    
    const request = new NextRequest('http://localhost:3000/api/workflow/1/execute', {
      method: 'POST',
      body: JSON.stringify({})
    })
    
    const context = { params: Promise.resolve({ id: '1' }) }
    const response = await POST(request, context)
    const data = await response.json()
    
    expect(response.status).toBe(500)
    expect(data.success).toBe(false)
    expect(data.error).toBe('Invalid JSON response')
  })
  
  it('비문자열 에러를 처리한다', async () => {
    mockFetch.mockRejectedValueOnce('String error')
    
    const request = new NextRequest('http://localhost:3000/api/workflow/1/execute', {
      method: 'POST',
      body: JSON.stringify({})
    })
    
    const context = { params: Promise.resolve({ id: '1' }) }
    const response = await POST(request, context)
    const data = await response.json()
    
    expect(response.status).toBe(500)
    expect(data.success).toBe(false)
    expect(data.error).toBe('Failed to execute workflow')
  })
  
  it('올바른 요청 헤더를 설정한다', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue({ success: true })
    } as any)
    
    const request = new NextRequest('http://localhost:3000/api/workflow/1/execute', {
      method: 'POST',
      body: JSON.stringify({})
    })
    
    const context = { params: Promise.resolve({ id: '1' }) }
    await POST(request, context)
    
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8001/execute-workflow',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
    )
  })
  
  it('워크플로우 엔진으로부터 오류 응답을 전달한다', async () => {
    const engineErrorResponse = {
      success: false,
      error: 'Workflow validation failed',
      details: {
        rule_id: 5,
        reason: 'Invalid condition'
      }
    }
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(engineErrorResponse)
    } as any)
    
    const request = new NextRequest('http://localhost:3000/api/workflow/1/execute', {
      method: 'POST',
      body: JSON.stringify({})
    })
    
    const context = { params: Promise.resolve({ id: '1' }) }
    const response = await POST(request, context)
    const data = await response.json()
    
    expect(response.status).toBe(200) // Engine returned valid response
    expect(data).toEqual(engineErrorResponse) // Pass through engine response
  })
})