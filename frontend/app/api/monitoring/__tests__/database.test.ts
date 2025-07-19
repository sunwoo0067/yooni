// Mock the database module before importing the route
jest.mock('@/lib/db', () => ({
  query: jest.fn(),
  getOne: jest.fn(),
  transaction: jest.fn(),
  getPoolStats: jest.fn(),
  healthCheck: jest.fn(),
}))

// Mock NextResponse
jest.mock('next/server', () => ({
  NextResponse: {
    json: jest.fn((data, options = {}) => ({
      json: async () => data,
      status: options.status || 200,
    })),
  },
}))

describe('/api/monitoring/database', () => {
  let mockGetPoolStats: jest.MockedFunction<any>
  let GET: any

  beforeEach(async () => {
    jest.clearAllMocks()
    mockGetPoolStats = require('@/lib/db').getPoolStats
    
    // Dynamic import to avoid NextRequest issues
    const databaseModule = await import('../database/route')
    GET = databaseModule.GET
  })

  it('데이터베이스 모니터링 정보를 반환한다', async () => {
    // Mock pool stats
    mockGetPoolStats.mockResolvedValue({
      totalCount: 8,
      idleCount: 5,
      waitingCount: 1
    })

    const mockRequest = {
      url: 'http://localhost:3000/api/monitoring/database',
      method: 'GET'
    }

    const response = await GET(mockRequest)
    const data = await response.json()

    expect(response.status).toBe(200)
    expect(data.poolSize).toBe(10)
    expect(data.activeConnections).toBe(3) // totalCount - idleCount
    expect(data.availableConnections).toBe(7) // poolSize - activeConnections
    expect(data.waitingConnections).toBe(1)
    expect(data.status).toBe('healthy')
  })

  it('풀 통계가 null인 경우를 처리한다', async () => {
    mockGetPoolStats.mockResolvedValue(null)

    const mockRequest = {
      url: 'http://localhost:3000/api/monitoring/database',
      method: 'GET'
    }

    const response = await GET(mockRequest)
    const data = await response.json()

    expect(data.activeConnections).toBe(0)
    expect(data.availableConnections).toBe(10)
    expect(data.waitingConnections).toBe(0)
    expect(data.totalConnections).toBe(0)
  })

  it('캐시 히트율을 올바르게 계산한다', async () => {
    mockGetPoolStats.mockResolvedValue({
      totalCount: 5,
      idleCount: 3,
      waitingCount: 0
    })

    // Mock 데이터베이스 통계 쿼리 결과
    const mockQuery = require('@/lib/db').query
    mockQuery.mockResolvedValue([{
      active_connections: 2,
      total_connections: 5,
      blocks_read: 1000,
      blocks_hit: 9000,
      avg_query_time: 25.5
    }])

    const mockRequest = {
      url: 'http://localhost:3000/api/monitoring/database',
      method: 'GET'
    }

    const response = await GET(mockRequest)
    const data = await response.json()

    // Cache hit rate = blocks_hit / (blocks_hit + blocks_read) * 100
    // = 9000 / (9000 + 1000) * 100 = 90%
    expect(data.cacheHitRate).toBe(90)
    expect(data.avgQueryTime).toBe(25.5)
  })

  it('pg_stat_statements가 없을 때 기본값을 사용한다', async () => {
    mockGetPoolStats.mockResolvedValue({
      totalCount: 3,
      idleCount: 1,
      waitingCount: 0
    })

    // pg_stat_statements 에러 시뮬레이션
    const mockQuery = require('@/lib/db').query
    mockQuery.mockRejectedValue(new Error('pg_stat_statements extension not available'))

    const mockRequest = {
      url: 'http://localhost:3000/api/monitoring/database',
      method: 'GET'
    }

    const response = await GET(mockRequest)
    const data = await response.json()

    expect(data.activeConnections).toBe(2) // totalCount - idleCount
    expect(data.totalConnections).toBe(3)  // totalCount 기본값 (3)
    expect(data.avgQueryTime).toBe(0)      // 기본값
    expect(data.status).toBe('healthy')
  })

  it('전체 에러 시 에러 응답을 반환한다', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
    mockGetPoolStats.mockRejectedValue(new Error('Pool connection failed'))

    const mockRequest = {
      url: 'http://localhost:3000/api/monitoring/database',
      method: 'GET'
    }

    const response = await GET(mockRequest)
    const data = await response.json()

    expect(data.poolSize).toBe(0)
    expect(data.activeConnections).toBe(0)
    expect(data.status).toBe('error')
    expect(data.error).toBe('Pool connection failed')
    expect(consoleSpy).toHaveBeenCalledWith('Database metrics error:', expect.any(Error))
    
    consoleSpy.mockRestore()
  })

  it('풀 통계 속성이 undefined인 경우를 안전하게 처리한다', async () => {
    mockGetPoolStats.mockResolvedValue({
      totalCount: undefined,
      idleCount: undefined,
      waitingCount: undefined
    })

    const mockRequest = {
      url: 'http://localhost:3000/api/monitoring/database',
      method: 'GET'
    }

    const response = await GET(mockRequest)
    const data = await response.json()

    expect(data.activeConnections).toBe(0)
    expect(data.availableConnections).toBe(10)
    expect(data.waitingConnections).toBe(0)
    expect(data.status).toBe('healthy')
  })

  it('연결 수 계산이 정확하다', async () => {
    mockGetPoolStats.mockResolvedValue({
      totalCount: 10,
      idleCount: 3,
      waitingCount: 2
    })

    const mockRequest = {
      url: 'http://localhost:3000/api/monitoring/database',
      method: 'GET'
    }

    const response = await GET(mockRequest)
    const data = await response.json()

    const expectedActiveConnections = 10 - 3 // totalCount - idleCount = 7
    const expectedAvailableConnections = 10 - expectedActiveConnections // poolSize - activeConnections = 3

    expect(data.activeConnections).toBe(expectedActiveConnections)
    expect(data.availableConnections).toBe(expectedAvailableConnections)
    expect(data.waitingConnections).toBe(2)
  })

  it('캐시 히트율이 0인 경우를 처리한다', async () => {
    mockGetPoolStats.mockResolvedValue({
      totalCount: 5,
      idleCount: 3,
      waitingCount: 0
    })

    const mockQuery = require('@/lib/db').query
    mockQuery.mockResolvedValue([{
      active_connections: 2,
      total_connections: 5,
      blocks_read: null,
      blocks_hit: null,
      avg_query_time: 0
    }])

    const mockRequest = {
      url: 'http://localhost:3000/api/monitoring/database',
      method: 'GET'
    }

    const response = await GET(mockRequest)
    const data = await response.json()

    expect(data.cacheHitRate).toBe(0)
    expect(data.avgQueryTime).toBe(0)
  })
})