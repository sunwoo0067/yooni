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

describe('/api/erp/stats', () => {
  let mockQuery: jest.MockedFunction<any>
  let GET: any

  beforeEach(async () => {
    jest.clearAllMocks()
    mockQuery = require('@/lib/db').query
    
    // Dynamic import to avoid NextRequest issues
    const statsModule = await import('../stats/route')
    GET = statsModule.GET
  })

  it('통계 데이터를 반환한다', async () => {
    // Mock database statistics
    mockQuery
      .mockResolvedValueOnce([{ // dbStats
        db_size: '1000000',
        table_count: '10',
        product_count: '1250',
        order_count: '100',
        customer_count: '50',
        supplier_count: '5'
      }])
      .mockResolvedValueOnce([]) // inventoryStats
      .mockResolvedValueOnce([]) // salesStats  
      .mockResolvedValueOnce([{ // operationsStats
        pending_orders: '5',
        processing_orders: '10',
        pending_shipments: '3',
        returns_to_process: '2'
      }])
      .mockResolvedValueOnce([{ // growthStats
        this_week: '100000',
        last_week: '90000'
      }])

    // Mock request object
    const mockRequest = {
      url: 'http://localhost:3000/api/erp/stats',
      method: 'GET'
    }

    const response = await GET(mockRequest)
    const data = await response.json()

    expect(response.status).toBe(200)
    expect(data.success).toBe(true)
    expect(data.data.database.record_counts.products).toBe(1250)
    expect(data.data.operations.pending_orders).toBe(5)
  })

  it('데이터베이스 오류 시 500을 반환한다', async () => {
    mockQuery.mockRejectedValueOnce(new Error('Database error'))

    const mockRequest = {
      url: 'http://localhost:3000/api/erp/stats',
      method: 'GET'
    }

    const response = await GET(mockRequest)
    const data = await response.json()

    expect(response.status).toBe(500)
    expect(data.success).toBe(false)
    expect(data.error).toBe('ERP 통계 조회 중 오류가 발생했습니다.')
  })

  it('올바른 SQL 쿼리를 실행한다', async () => {
    mockQuery
      .mockResolvedValueOnce([{}]) // dbStats
      .mockResolvedValueOnce([]) // inventoryStats
      .mockResolvedValueOnce([]) // salesStats
      .mockResolvedValueOnce([{}]) // operationsStats
      .mockResolvedValueOnce([{}]) // growthStats

    const mockRequest = {
      url: 'http://localhost:3000/api/erp/stats',
      method: 'GET'
    }

    await GET(mockRequest)

    expect(mockQuery).toHaveBeenCalledWith(
      expect.stringContaining('pg_database_size(current_database()) as db_size')
    )
    expect(mockQuery).toHaveBeenCalledWith(
      expect.stringContaining('FROM market_products mp')
    )
  })
})