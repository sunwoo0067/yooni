import { GET } from '../route'
import { NextRequest } from 'next/server'

describe('/api/monitoring/timeseries', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  it('기본 시계열 데이터를 반환한다', async () => {
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data).toHaveProperty('system')
    expect(data).toHaveProperty('network')
    expect(data).toHaveProperty('database')
    expect(data).toHaveProperty('business')
    
    expect(Array.isArray(data.system)).toBe(true)
    expect(Array.isArray(data.network)).toBe(true)
    expect(Array.isArray(data.database)).toBe(true)
    expect(Array.isArray(data.business)).toBe(true)
  })
  
  it('1시간 범위의 데이터를 올바르게 생성한다', async () => {
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries?range=1h')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.system).toHaveLength(60) // 60 data points for 1 hour
    expect(data.network).toHaveLength(60)
    expect(data.database).toHaveLength(60)
    expect(data.business).toHaveLength(60)
    
    // Verify data structure
    expect(data.system[0]).toHaveProperty('timestamp')
    expect(data.system[0]).toHaveProperty('cpu')
    expect(data.system[0]).toHaveProperty('memory')
    expect(data.system[0]).toHaveProperty('disk')
  })
  
  it('5분 범위의 데이터를 올바르게 생성한다', async () => {
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries?range=5m')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.system).toHaveLength(30) // 30 data points for 5 minutes
    expect(data.network).toHaveLength(30)
    expect(data.database).toHaveLength(30)
    expect(data.business).toHaveLength(30)
  })
  
  it('24시간 범위의 데이터를 올바르게 생성한다', async () => {
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries?range=24h')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.system).toHaveLength(144) // 144 data points for 24 hours (10min intervals)
    expect(data.network).toHaveLength(144)
    expect(data.database).toHaveLength(144)
    expect(data.business).toHaveLength(144)
  })
  
  it('7일 범위의 데이터를 올바르게 생성한다', async () => {
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries?range=7d')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.system).toHaveLength(168) // 168 data points for 7 days (1hour intervals)
    expect(data.network).toHaveLength(168)
    expect(data.database).toHaveLength(168)
    expect(data.business).toHaveLength(168)
  })
  
  it('시스템 메트릭 데이터 구조를 확인한다', async () => {
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    
    const systemPoint = data.system[0]
    expect(systemPoint).toHaveProperty('timestamp')
    expect(systemPoint).toHaveProperty('cpu')
    expect(systemPoint).toHaveProperty('memory')
    expect(systemPoint).toHaveProperty('disk')
    
    expect(typeof systemPoint.timestamp).toBe('string')
    expect(typeof systemPoint.cpu).toBe('number')
    expect(typeof systemPoint.memory).toBe('number')
    expect(typeof systemPoint.disk).toBe('number')
    
    // Verify timestamp is valid ISO string
    expect(() => new Date(systemPoint.timestamp)).not.toThrow()
    expect(new Date(systemPoint.timestamp)).toBeInstanceOf(Date)
  })
  
  it('네트워크 메트릭 데이터 구조를 확인한다', async () => {
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    
    const networkPoint = data.network[0]
    expect(networkPoint).toHaveProperty('timestamp')
    expect(networkPoint).toHaveProperty('inbound')
    expect(networkPoint).toHaveProperty('outbound')
    
    expect(typeof networkPoint.timestamp).toBe('string')
    expect(typeof networkPoint.inbound).toBe('number')
    expect(typeof networkPoint.outbound).toBe('number')
    
    // Verify values are within expected ranges
    expect(networkPoint.inbound).toBeGreaterThanOrEqual(500)
    expect(networkPoint.inbound).toBeLessThanOrEqual(1500)
    expect(networkPoint.outbound).toBeGreaterThanOrEqual(300)
    expect(networkPoint.outbound).toBeLessThanOrEqual(1100)
  })
  
  it('데이터베이스 메트릭 데이터 구조를 확인한다', async () => {
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    
    const dbPoint = data.database[0]
    expect(dbPoint).toHaveProperty('timestamp')
    expect(dbPoint).toHaveProperty('connections')
    expect(dbPoint).toHaveProperty('queries')
    expect(dbPoint).toHaveProperty('slow_queries')
    
    expect(typeof dbPoint.timestamp).toBe('string')
    expect(typeof dbPoint.connections).toBe('number')
    expect(typeof dbPoint.queries).toBe('number')
    expect(typeof dbPoint.slow_queries).toBe('number')
    
    // Verify values are within expected ranges
    expect(dbPoint.connections).toBeGreaterThanOrEqual(5)
    expect(dbPoint.connections).toBeLessThanOrEqual(15)
    expect(dbPoint.queries).toBeGreaterThanOrEqual(50)
    expect(dbPoint.queries).toBeLessThanOrEqual(150)
    expect(dbPoint.slow_queries).toBeGreaterThanOrEqual(0)
    expect(dbPoint.slow_queries).toBeLessThanOrEqual(5)
  })
  
  it('비즈니스 메트릭 데이터 구조를 확인한다', async () => {
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    
    const businessPoint = data.business[0]
    expect(businessPoint).toHaveProperty('timestamp')
    expect(businessPoint).toHaveProperty('orders')
    expect(businessPoint).toHaveProperty('revenue')
    expect(businessPoint).toHaveProperty('users')
    
    expect(typeof businessPoint.timestamp).toBe('string')
    expect(typeof businessPoint.orders).toBe('number')
    expect(typeof businessPoint.revenue).toBe('number')
    expect(typeof businessPoint.users).toBe('number')
    
    // Verify values are within expected ranges
    expect(businessPoint.orders).toBeGreaterThanOrEqual(20)
    expect(businessPoint.orders).toBeLessThanOrEqual(70)
    expect(businessPoint.revenue).toBeGreaterThanOrEqual(100000)
    expect(businessPoint.revenue).toBeLessThanOrEqual(600000)
    expect(businessPoint.users).toBeGreaterThanOrEqual(500)
    expect(businessPoint.users).toBeLessThanOrEqual(1500)
  })
  
  it('타임스탬프가 시간순으로 정렬되어 있다', async () => {
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    
    // Check system data timestamps are in ascending order
    for (let i = 1; i < data.system.length; i++) {
      const prevTime = new Date(data.system[i - 1].timestamp).getTime()
      const currTime = new Date(data.system[i].timestamp).getTime()
      expect(currTime).toBeGreaterThan(prevTime)
    }
    
    // Check network data timestamps are in ascending order
    for (let i = 1; i < data.network.length; i++) {
      const prevTime = new Date(data.network[i - 1].timestamp).getTime()
      const currTime = new Date(data.network[i].timestamp).getTime()
      expect(currTime).toBeGreaterThan(prevTime)
    }
  })
  
  it('모든 카테고리의 타임스탬프가 동일하다', async () => {
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    
    // Verify all categories have the same timestamps
    for (let i = 0; i < data.system.length; i++) {
      expect(data.system[i].timestamp).toBe(data.network[i].timestamp)
      expect(data.system[i].timestamp).toBe(data.database[i].timestamp)
      expect(data.system[i].timestamp).toBe(data.business[i].timestamp)
    }
  })
  
  it('CPU 값이 합리적인 범위 내에 있다', async () => {
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    
    data.system.forEach(point => {
      expect(point.cpu).toBeGreaterThanOrEqual(0)
      expect(point.cpu).toBeLessThanOrEqual(100)
    })
  })
  
  it('메모리 값이 합리적인 범위 내에 있다', async () => {
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    
    data.system.forEach(point => {
      expect(point.memory).toBeGreaterThanOrEqual(0)
      expect(point.memory).toBeLessThanOrEqual(100)
    })
  })
  
  it('디스크 값이 합리적인 범위 내에 있다', async () => {
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    
    data.system.forEach(point => {
      expect(point.disk).toBeGreaterThanOrEqual(0)
      expect(point.disk).toBeLessThanOrEqual(100)
    })
  })
  
  it('잘못된 범위 파라미터를 기본값으로 처리한다', async () => {
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries?range=invalid')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    // Should default to 1h behavior (60 points)
    expect(data.system).toHaveLength(60)
  })
  
  it('빈 범위 파라미터를 기본값으로 처리한다', async () => {
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries?range=')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    // Should default to 1h behavior (60 points)
    expect(data.system).toHaveLength(60)
  })
  
  it('타임스탬프가 현재 시간에 가깝다', async () => {
    const beforeRequest = Date.now()
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries')
    const response = await GET(request)
    const data = await response.json()
    const afterRequest = Date.now()
    
    expect(response.status).toBe(200)
    
    // The last (most recent) timestamp should be close to current time
    const lastTimestamp = new Date(data.system[data.system.length - 1].timestamp).getTime()
    
    // Allow for some processing time (5 seconds)
    expect(lastTimestamp).toBeGreaterThanOrEqual(beforeRequest - 5000)
    expect(lastTimestamp).toBeLessThanOrEqual(afterRequest + 5000)
  })
  
  it('시계열 생성 함수에서 오류가 발생해도 처리한다', async () => {
    // Mock Math.random to throw an error
    const originalRandom = Math.random
    Math.random = jest.fn(() => {
      throw new Error('Random generation error')
    })
    
    try {
      const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to fetch timeseries data')
    } finally {
      // Restore original Math.random
      Math.random = originalRandom
    }
  })
  
  it('대용량 범위 요청을 처리한다', async () => {
    const request = new NextRequest('http://localhost:3000/api/monitoring/timeseries?range=7d')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.system).toHaveLength(168) // 7 days * 24 hours
    
    // Verify performance - should complete reasonably fast
    // (This is more of an integration test)
    expect(data.system.length).toBeGreaterThan(0)
    expect(data.network.length).toBeGreaterThan(0)
    expect(data.database.length).toBeGreaterThan(0)
    expect(data.business.length).toBeGreaterThan(0)
  })
})