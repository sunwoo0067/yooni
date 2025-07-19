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

describe('/api/dashboard/stats', () => {
  let mockQuery: jest.MockedFunction<any>
  let mockGetOne: jest.MockedFunction<any>
  let GET: any

  beforeEach(async () => {
    jest.clearAllMocks()
    mockQuery = require('@/lib/db').query
    mockGetOne = require('@/lib/db').getOne
    
    // Dynamic import to avoid NextRequest issues
    const statsModule = await import('../stats/route')
    GET = statsModule.GET
  })

  it('대시보드 통계를 정상적으로 반환한다', async () => {
    // Mock database responses
    mockGetOne
      .mockResolvedValueOnce({ count: '1250' }) // totalProducts
      .mockResolvedValueOnce({ count: '1000' }) // activeProducts

    // Mock query responses for additional stats
    mockQuery
      .mockResolvedValueOnce([]) // today orders (will error and use defaults)
      .mockResolvedValueOnce([]) // today revenue (will error and use defaults)
      .mockResolvedValueOnce([   // supplier stats
        { supplier: 'Supplier 1', count: '500' },
        { supplier: 'Supplier 2', count: '750' }
      ])
      .mockResolvedValueOnce([   // status stats
        { status: 'active', count: '1000' },
        { status: 'inactive', count: '250' }
      ])
      .mockResolvedValueOnce([   // inventory stats
        { in_stock: '800', out_of_stock: '200', low_stock: '50' }
      ])

    // Mock request
    const mockRequest = {
      url: 'http://localhost:3000/api/dashboard/stats',
      method: 'GET'
    }

    const response = await GET(mockRequest)
    const data = await response.json()

    expect(response.status).toBe(200)
    expect(data.success).toBe(true)
    expect(data.data.products.total).toBe(1250)
    expect(data.data.products.active).toBe(1000)
    expect(data.data.products.activePercentage).toBe('80.00')
    expect(data.data.suppliers).toHaveLength(2)
    expect(data.data.status).toHaveLength(2)
  })

  it('총 상품 수와 활성 상품 수를 올바르게 계산한다', async () => {
    mockGetOne
      .mockResolvedValueOnce({ count: '2000' }) // totalProducts
      .mockResolvedValueOnce({ count: '1500' }) // activeProducts

    // Mock query responses
    mockQuery
      .mockResolvedValueOnce([]) // today orders
      .mockResolvedValueOnce([]) // today revenue
      .mockResolvedValueOnce([]) // supplier stats
      .mockResolvedValueOnce([]) // status stats
      .mockResolvedValueOnce([{ in_stock: '0', out_of_stock: '0', low_stock: '0' }]) // inventory stats

    const mockRequest = {
      url: 'http://localhost:3000/api/dashboard/stats',
      method: 'GET'
    }

    const response = await GET(mockRequest)
    const data = await response.json()

    expect(data.data.products.total).toBe(2000)
    expect(data.data.products.active).toBe(1500)
    expect(data.data.products.activePercentage).toBe('75.00')
  })

  it('상품이 없을 때 0%를 반환한다', async () => {
    mockGetOne
      .mockResolvedValueOnce({ count: '0' }) // totalProducts
      .mockResolvedValueOnce({ count: '0' }) // activeProducts

    // Mock query responses
    mockQuery
      .mockResolvedValueOnce([]) // today orders
      .mockResolvedValueOnce([]) // today revenue
      .mockResolvedValueOnce([]) // supplier stats
      .mockResolvedValueOnce([]) // status stats
      .mockResolvedValueOnce([{ in_stock: '0', out_of_stock: '0', low_stock: '0' }]) // inventory stats

    const mockRequest = {
      url: 'http://localhost:3000/api/dashboard/stats',
      method: 'GET'
    }

    const response = await GET(mockRequest)
    const data = await response.json()

    expect(data.data.products.total).toBe(0)
    expect(data.data.products.active).toBe(0)
    expect(data.data.products.activePercentage).toBe('0')
  })

  it('null 값을 안전하게 처리한다', async () => {
    mockGetOne
      .mockResolvedValueOnce(null) // totalProducts
      .mockResolvedValueOnce(null) // activeProducts

    // Mock query responses
    mockQuery
      .mockResolvedValueOnce([]) // today orders
      .mockResolvedValueOnce([]) // today revenue
      .mockResolvedValueOnce([]) // supplier stats
      .mockResolvedValueOnce([]) // status stats
      .mockResolvedValueOnce([{ in_stock: '0', out_of_stock: '0', low_stock: '0' }]) // inventory stats

    const mockRequest = {
      url: 'http://localhost:3000/api/dashboard/stats',
      method: 'GET'
    }

    const response = await GET(mockRequest)
    const data = await response.json()

    expect(data.data.products.total).toBe(0)
    expect(data.data.products.active).toBe(0)
    expect(data.data.products.activePercentage).toBe('0')
  })

  it('데이터베이스 에러를 적절히 처리한다', async () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
    mockGetOne.mockRejectedValueOnce(new Error('Database connection failed'))

    const mockRequest = {
      url: 'http://localhost:3000/api/dashboard/stats',
      method: 'GET'
    }

    const response = await GET(mockRequest)
    const data = await response.json()

    expect(response.status).toBe(500)
    expect(data.success).toBe(false)
    expect(data.error).toBe('Failed to fetch dashboard stats')
    expect(data.details).toBe('Database connection failed')
    expect(consoleSpy).toHaveBeenCalledWith('Dashboard stats error:', expect.any(Error))
    
    consoleSpy.mockRestore()
  })

  it('올바른 SQL 쿼리를 실행한다', async () => {
    mockGetOne
      .mockResolvedValueOnce({ count: '100' })
      .mockResolvedValueOnce({ count: '80' })

    // Mock query responses
    mockQuery
      .mockResolvedValueOnce([]) // today orders
      .mockResolvedValueOnce([]) // today revenue
      .mockResolvedValueOnce([]) // supplier stats
      .mockResolvedValueOnce([]) // status stats
      .mockResolvedValueOnce([{ in_stock: '0', out_of_stock: '0', low_stock: '0' }]) // inventory stats

    const mockRequest = {
      url: 'http://localhost:3000/api/dashboard/stats',
      method: 'GET'
    }

    await GET(mockRequest)

    expect(mockGetOne).toHaveBeenCalledWith(
      'SELECT COUNT(*) as count FROM products'
    )
    expect(mockGetOne).toHaveBeenCalledWith(
      "SELECT COUNT(*) as count FROM products WHERE status = 'active'"
    )
  })

  it('퍼센티지 계산이 정확하다', async () => {
    // Test case 1: 정확한 나누어떨어지는 경우
    mockGetOne
      .mockResolvedValueOnce({ count: '400' })
      .mockResolvedValueOnce({ count: '100' })

    // Mock query responses for first test
    mockQuery
      .mockResolvedValueOnce([]) // today orders
      .mockResolvedValueOnce([]) // today revenue
      .mockResolvedValueOnce([]) // supplier stats
      .mockResolvedValueOnce([]) // status stats
      .mockResolvedValueOnce([{ in_stock: '0', out_of_stock: '0', low_stock: '0' }]) // inventory stats

    let response = await GET({ url: 'http://localhost:3000/api/dashboard/stats', method: 'GET' })
    let data = await response.json()
    expect(data.data.products.activePercentage).toBe('25.00')

    // Test case 2: 소수점이 있는 경우
    jest.clearAllMocks()
    mockGetOne
      .mockResolvedValueOnce({ count: '300' })
      .mockResolvedValueOnce({ count: '100' })

    // Mock query responses for second test
    mockQuery
      .mockResolvedValueOnce([]) // today orders
      .mockResolvedValueOnce([]) // today revenue
      .mockResolvedValueOnce([]) // supplier stats
      .mockResolvedValueOnce([]) // status stats
      .mockResolvedValueOnce([{ in_stock: '0', out_of_stock: '0', low_stock: '0' }]) // inventory stats

    response = await GET({ url: 'http://localhost:3000/api/dashboard/stats', method: 'GET' })
    data = await response.json()
    expect(data.data.products.activePercentage).toBe('33.33')
  })

  it('매우 큰 숫자도 정확히 처리한다', async () => {
    mockGetOne
      .mockResolvedValueOnce({ count: '1000000' }) // 1M products
      .mockResolvedValueOnce({ count: '750000' })  // 750K active

    // Mock query responses
    mockQuery
      .mockResolvedValueOnce([]) // today orders
      .mockResolvedValueOnce([]) // today revenue
      .mockResolvedValueOnce([]) // supplier stats
      .mockResolvedValueOnce([]) // status stats
      .mockResolvedValueOnce([{ in_stock: '0', out_of_stock: '0', low_stock: '0' }]) // inventory stats

    const mockRequest = {
      url: 'http://localhost:3000/api/dashboard/stats',
      method: 'GET'
    }

    const response = await GET(mockRequest)
    const data = await response.json()

    expect(data.data.products.total).toBe(1000000)
    expect(data.data.products.active).toBe(750000)
    expect(data.data.products.activePercentage).toBe('75.00')
  })
})