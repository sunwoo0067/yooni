import { GET, POST } from '../route'
import { NextRequest } from 'next/server'

// Mock the logger module
jest.mock('@/lib/logger/structured-logger', () => ({
  getLogger: jest.fn(() => ({
    error: jest.fn()
  }))
}))

describe('/api/monitoring/api', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Reset any global state between tests
    jest.resetModules()
  })
  
  describe('GET', () => {
    it('빈 메트릭에서 기본값을 반환한다', async () => {
      const request = new NextRequest('http://localhost:3000/api/monitoring/api')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data).toEqual({
        requestCount: 0,
        errorRate: 0,
        avgResponseTime: 0,
        endpoints: [],
        timeRange: '1h',
        lastReset: expect.any(String)
      })
      expect(new Date(data.lastReset)).toBeInstanceOf(Date)
    })
    
    it('시간 범위 파라미터를 처리한다', async () => {
      const request = new NextRequest('http://localhost:3000/api/monitoring/api?range=24h')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.timeRange).toBe('24h')
    })
    
    it('기본 시간 범위를 사용한다', async () => {
      const request = new NextRequest('http://localhost:3000/api/monitoring/api')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.timeRange).toBe('1h')
    })
    
    it('다양한 범위 값을 처리한다', async () => {
      const ranges = ['1h', '24h', '7d', '30d', 'custom']
      
      for (const range of ranges) {
        const request = new NextRequest(`http://localhost:3000/api/monitoring/api?range=${range}`)
        const response = await GET(request)
        const data = await response.json()
        
        expect(response.status).toBe(200)
        expect(data.timeRange).toBe(range)
      }
    })
  })
  
  describe('POST', () => {
    const createRequest = (body: any) => {
      return new NextRequest('http://localhost:3000/api/monitoring/api', {
        method: 'POST',
        body: JSON.stringify(body)
      })
    }
    
    it('새 메트릭을 성공적으로 기록한다', async () => {
      const metricData = {
        endpoint: '/api/suppliers',
        method: 'GET',
        status: 200,
        duration: 150
      }
      
      const request = createRequest(metricData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
    })
    
    it('메트릭 기록 후 집계를 올바르게 처리한다', async () => {
      // Record some metrics first
      const metrics = [
        { endpoint: '/api/products', method: 'GET', status: 200, duration: 120 },
        { endpoint: '/api/products', method: 'GET', status: 200, duration: 180 },
        { endpoint: '/api/products', method: 'POST', status: 201, duration: 250 },
        { endpoint: '/api/orders', method: 'GET', status: 404, duration: 50 },
        { endpoint: '/api/orders', method: 'GET', status: 500, duration: 300 }
      ]
      
      // Record all metrics
      for (const metric of metrics) {
        const request = createRequest(metric)
        await POST(request)
      }
      
      // Get aggregated data
      const getRequest = new NextRequest('http://localhost:3000/api/monitoring/api')
      const getResponse = await GET(getRequest)
      const data = await getResponse.json()
      
      expect(getResponse.status).toBe(200)
      expect(data.requestCount).toBe(5)
      expect(data.errorRate).toBe(40) // 2 errors out of 5 requests
      expect(data.avgResponseTime).toBe(180) // (120+180+250+50+300)/5
      expect(data.endpoints).toHaveLength(3) // 3 unique endpoint+method combinations
    })
    
    it('에러 상태 코드를 올바르게 분류한다', async () => {
      const errorMetrics = [
        { endpoint: '/api/test', method: 'GET', status: 400, duration: 100 },
        { endpoint: '/api/test', method: 'GET', status: 404, duration: 50 },
        { endpoint: '/api/test', method: 'GET', status: 500, duration: 200 },
        { endpoint: '/api/test', method: 'GET', status: 200, duration: 150 }
      ]
      
      for (const metric of errorMetrics) {
        await POST(createRequest(metric))
      }
      
      const getRequest = new NextRequest('http://localhost:3000/api/monitoring/api')
      const getResponse = await GET(getRequest)
      const data = await getResponse.json()
      
      expect(data.errorRate).toBe(75) // 3 errors out of 4 requests
      expect(data.endpoints[0].errorRate).toBe(75)
    })
    
    it('상태 코드 그룹화를 올바르게 처리한다', async () => {
      const statusMetrics = [
        { endpoint: '/api/test', method: 'GET', status: 200, duration: 100 },
        { endpoint: '/api/test', method: 'GET', status: 201, duration: 120 },
        { endpoint: '/api/test', method: 'GET', status: 400, duration: 80 },
        { endpoint: '/api/test', method: 'GET', status: 404, duration: 60 },
        { endpoint: '/api/test', method: 'GET', status: 500, duration: 200 }
      ]
      
      for (const metric of statusMetrics) {
        await POST(createRequest(metric))
      }
      
      const getRequest = new NextRequest('http://localhost:3000/api/monitoring/api')
      const getResponse = await GET(getRequest)
      const data = await getResponse.json()
      
      const endpoint = data.endpoints[0]
      expect(endpoint.statuses).toEqual({
        '2xx': 2, // 200, 201
        '4xx': 2, // 400, 404  
        '5xx': 1  // 500
      })
    })
    
    it('평균 응답 시간을 올바르게 계산한다', async () => {
      const timingMetrics = [
        { endpoint: '/api/timing', method: 'GET', status: 200, duration: 100 },
        { endpoint: '/api/timing', method: 'GET', status: 200, duration: 200 },
        { endpoint: '/api/timing', method: 'GET', status: 200, duration: 300 }
      ]
      
      for (const metric of timingMetrics) {
        await POST(createRequest(metric))
      }
      
      const getRequest = new NextRequest('http://localhost:3000/api/monitoring/api')
      const getResponse = await GET(getRequest)
      const data = await getResponse.json()
      
      expect(data.avgResponseTime).toBe(200) // (100+200+300)/3
      expect(data.endpoints[0].avgTime).toBe(200)
    })
    
    it('여러 엔드포인트를 올바르게 집계한다', async () => {
      const multiEndpointMetrics = [
        { endpoint: '/api/users', method: 'GET', status: 200, duration: 100 },
        { endpoint: '/api/users', method: 'POST', status: 201, duration: 200 },
        { endpoint: '/api/products', method: 'GET', status: 200, duration: 150 },
        { endpoint: '/api/orders', method: 'GET', status: 404, duration: 50 }
      ]
      
      for (const metric of multiEndpointMetrics) {
        await POST(createRequest(metric))
      }
      
      const getRequest = new NextRequest('http://localhost:3000/api/monitoring/api')
      const getResponse = await GET(getRequest)
      const data = await getResponse.json()
      
      expect(data.endpoints).toHaveLength(4)
      expect(data.endpoints.map(e => e.endpoint)).toContain('GET /api/users')
      expect(data.endpoints.map(e => e.endpoint)).toContain('POST /api/users')
      expect(data.endpoints.map(e => e.endpoint)).toContain('GET /api/products')
      expect(data.endpoints.map(e => e.endpoint)).toContain('GET /api/orders')
    })
    
    it('상위 10개 엔드포인트만 반환한다', async () => {
      // Create 15 different endpoints
      for (let i = 0; i < 15; i++) {
        const metrics = Array(i + 1).fill(null).map(() => ({
          endpoint: `/api/endpoint${i}`,
          method: 'GET',
          status: 200,
          duration: 100
        }))
        
        for (const metric of metrics) {
          await POST(createRequest(metric))
        }
      }
      
      const getRequest = new NextRequest('http://localhost:3000/api/monitoring/api')
      const getResponse = await GET(getRequest)
      const data = await getResponse.json()
      
      expect(data.endpoints).toHaveLength(10)
      // Should be sorted by request count (descending)
      expect(data.endpoints[0].count).toBeGreaterThan(data.endpoints[1].count)
    })
    
    it('잘못된 메트릭 데이터를 처리한다', async () => {
      const invalidData = {
        // Missing required fields
        endpoint: '/api/test'
        // method, status, duration missing
      }
      
      const request = createRequest(invalidData)
      const response = await POST(request)
      
      // Should handle gracefully - specific behavior depends on implementation
      expect(response.status).toBe(200) // or 400 if validation is added
    })
    
    it('메트릭 기록 중 오류를 처리한다', async () => {
      // Test with malformed JSON
      const request = new NextRequest('http://localhost:3000/api/monitoring/api', {
        method: 'POST',
        body: 'invalid json'
      })
      
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to record metric')
    })
    
    it('0 지속시간 메트릭을 처리한다', async () => {
      const zeroTimeMetric = {
        endpoint: '/api/fast',
        method: 'GET',
        status: 200,
        duration: 0
      }
      
      const request = createRequest(zeroTimeMetric)
      const response = await POST(request)
      
      expect(response.status).toBe(200)
      
      const getRequest = new NextRequest('http://localhost:3000/api/monitoring/api')
      const getResponse = await GET(getRequest)
      const data = await getResponse.json()
      
      expect(data.endpoints[0].avgTime).toBe(0)
    })
    
    it('대용량 지속시간 메트릭을 처리한다', async () => {
      const slowMetric = {
        endpoint: '/api/slow',
        method: 'GET',
        status: 200,
        duration: 30000 // 30 seconds
      }
      
      const request = createRequest(slowMetric)
      const response = await POST(request)
      
      expect(response.status).toBe(200)
      
      const getRequest = new NextRequest('http://localhost:3000/api/monitoring/api')
      const getResponse = await GET(getRequest)
      const data = await getResponse.json()
      
      expect(data.endpoints[0].avgTime).toBe(30000)
      expect(data.avgResponseTime).toBe(30000)
    })
    
    it('동일한 엔드포인트의 여러 메트릭을 누적한다', async () => {
      const sameEndpointMetrics = [
        { endpoint: '/api/same', method: 'GET', status: 200, duration: 100 },
        { endpoint: '/api/same', method: 'GET', status: 200, duration: 150 },
        { endpoint: '/api/same', method: 'GET', status: 404, duration: 80 }
      ]
      
      for (const metric of sameEndpointMetrics) {
        await POST(createRequest(metric))
      }
      
      const getRequest = new NextRequest('http://localhost:3000/api/monitoring/api')
      const getResponse = await GET(getRequest)
      const data = await getResponse.json()
      
      expect(data.endpoints).toHaveLength(1)
      expect(data.endpoints[0].count).toBe(3)
      expect(data.endpoints[0].avgTime).toBeCloseTo(110) // (100+150+80)/3
      expect(data.endpoints[0].errorRate).toBeCloseTo(33.33) // 1 error out of 3
    })
  })
})