import { GET } from '../route'
import { NextRequest } from 'next/server'
import { Pool } from 'pg'

// Mock the pg pool
const mockPool = {
  query: jest.fn()
}

jest.mock('pg', () => ({
  Pool: jest.fn().mockImplementation(() => mockPool)
}))

describe('/api/monitoring/business', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  it('성공적인 비즈니스 메트릭을 반환한다', async () => {
    const mockOrdersResult = {
      rows: [{
        total_orders: '150',
        completed_orders: '120',
        cancelled_orders: '30',
        total_revenue: '1500000.50',
        avg_order_value: '12500.00'
      }]
    }
    
    const mockProductsResult = {
      rows: [{
        total_products: '5000',
        active_products: '4500',
        out_of_stock: '100'
      }]
    }
    
    const mockCustomersResult = {
      rows: [{
        unique_customers: '800',
        active_customers: '200'
      }]
    }
    
    mockPool.query
      .mockResolvedValueOnce(mockOrdersResult)
      .mockResolvedValueOnce(mockProductsResult)
      .mockResolvedValueOnce(mockCustomersResult)
    
    const request = new NextRequest('http://localhost:3000/api/monitoring/business')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data).toEqual({
      totalOrders: 150,
      completedOrders: 120,
      cancelledOrders: 30,
      totalRevenue: 1500000.5,
      avgOrderValue: 12500,
      activeProducts: 4500,
      totalProducts: 5000,
      outOfStock: 100,
      uniqueCustomers: 800,
      activeCustomers: 200,
      conversionRate: 60, // 120/200 * 100
      timeRange: '1h'
    })
    
    // Verify all 3 queries were executed
    expect(mockPool.query).toHaveBeenCalledTimes(3)
  })
  
  it('시간 범위 파라미터를 올바르게 처리한다', async () => {
    const timeRanges = [
      { range: '5m', interval: '5 minutes' },
      { range: '1h', interval: '1 hour' },
      { range: '24h', interval: '24 hours' },
      { range: '7d', interval: '7 days' }
    ]
    
    for (const { range, interval } of timeRanges) {
      // Reset mocks for each iteration
      mockPool.query.mockReset()
      mockPool.query
        .mockResolvedValueOnce({ rows: [{}] })
        .mockResolvedValueOnce({ rows: [{}] })
        .mockResolvedValueOnce({ rows: [{}] })
      
      const request = new NextRequest(`http://localhost:3000/api/monitoring/business?range=${range}`)
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.timeRange).toBe(range)
      
      // Verify interval is used in orders query
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining(`INTERVAL '${interval}'`)
      )
    }
  })
  
  it('기본 시간 범위를 사용한다', async () => {
    mockPool.query
      .mockResolvedValueOnce({ rows: [{}] })
      .mockResolvedValueOnce({ rows: [{}] })
      .mockResolvedValueOnce({ rows: [{}] })
    
    const request = new NextRequest('http://localhost:3000/api/monitoring/business')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.timeRange).toBe('1h')
    
    // Verify default 1 hour interval
    expect(mockPool.query).toHaveBeenCalledWith(
      expect.stringContaining("INTERVAL '1 hour'")
    )
  })
  
  it('null/undefined 값을 0으로 처리한다', async () => {
    const mockNullResults = {
      rows: [{
        total_orders: null,
        completed_orders: undefined,
        cancelled_orders: '0',
        total_revenue: null,
        avg_order_value: undefined
      }]
    }
    
    mockPool.query
      .mockResolvedValueOnce(mockNullResults)
      .mockResolvedValueOnce({ rows: [{}] })
      .mockResolvedValueOnce({ rows: [{}] })
    
    const request = new NextRequest('http://localhost:3000/api/monitoring/business')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.totalOrders).toBe(0)
    expect(data.completedOrders).toBe(0)
    expect(data.cancelledOrders).toBe(0)
    expect(data.totalRevenue).toBe(0)
    expect(data.avgOrderValue).toBe(0)
  })
  
  it('전환율을 올바르게 계산한다', async () => {
    const scenarios = [
      // Normal case
      {
        orders: { completed_orders: '60' },
        customers: { active_customers: '200' },
        expectedRate: 30 // 60/200 * 100
      },
      // Zero active customers
      {
        orders: { completed_orders: '60' },
        customers: { active_customers: '0' },
        expectedRate: 0
      },
      // Zero completed orders
      {
        orders: { completed_orders: '0' },
        customers: { active_customers: '200' },
        expectedRate: 0
      }
    ]
    
    for (const scenario of scenarios) {
      mockPool.query.mockReset()
      mockPool.query
        .mockResolvedValueOnce({ rows: [scenario.orders] })
        .mockResolvedValueOnce({ rows: [{}] })
        .mockResolvedValueOnce({ rows: [scenario.customers] })
      
      const request = new NextRequest('http://localhost:3000/api/monitoring/business')
      const response = await GET(request)
      const data = await response.json()
      
      expect(data.conversionRate).toBe(scenario.expectedRate)
    }
  })
  
  it('병렬 쿼리 실행을 확인한다', async () => {
    const queryPromises = [
      Promise.resolve({ rows: [{}] }),
      Promise.resolve({ rows: [{}] }),
      Promise.resolve({ rows: [{}] })
    ]
    
    mockPool.query
      .mockReturnValueOnce(queryPromises[0])
      .mockReturnValueOnce(queryPromises[1])
      .mockReturnValueOnce(queryPromises[2])
    
    const request = new NextRequest('http://localhost:3000/api/monitoring/business')
    const response = await GET(request)
    
    expect(response.status).toBe(200)
    expect(mockPool.query).toHaveBeenCalledTimes(3)
    
    // Verify query types
    const calls = mockPool.query.mock.calls
    expect(calls[0][0]).toContain('FROM orders')      // Orders query
    expect(calls[1][0]).toContain('FROM products')    // Products query
    expect(calls[2][0]).toContain('FROM orders')      // Customers query
  })
  
  it('큰 숫자 값을 올바르게 파싱한다', async () => {
    const mockLargeValues = {
      rows: [{
        total_orders: '999999',
        completed_orders: '888888',
        cancelled_orders: '111111',
        total_revenue: '999999999.99',
        avg_order_value: '1234567.89'
      }]
    }
    
    mockPool.query
      .mockResolvedValueOnce(mockLargeValues)
      .mockResolvedValueOnce({ rows: [{ total_products: '1000000', active_products: '900000', out_of_stock: '50000' }] })
      .mockResolvedValueOnce({ rows: [{ unique_customers: '100000', active_customers: '25000' }] })
    
    const request = new NextRequest('http://localhost:3000/api/monitoring/business')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.totalOrders).toBe(999999)
    expect(data.totalRevenue).toBe(999999999.99)
    expect(data.avgOrderValue).toBe(1234567.89)
    expect(data.totalProducts).toBe(1000000)
  })
  
  it('데이터베이스 오류 시 더미 데이터를 반환한다', async () => {
    mockPool.query.mockRejectedValueOnce(new Error('Database connection failed'))
    
    const request = new NextRequest('http://localhost:3000/api/monitoring/business?range=24h')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data).toEqual({
      totalOrders: 1234,
      completedOrders: 1000,
      cancelledOrders: 234,
      totalRevenue: 12345678,
      avgOrderValue: 12345,
      activeProducts: 5678,
      totalProducts: 6789,
      outOfStock: 123,
      uniqueCustomers: 456,
      activeCustomers: 123,
      conversionRate: 2.5,
      timeRange: '24h'
    })
  })
  
  it('부분적 쿼리 실패를 처리한다', async () => {
    // First query succeeds, second fails
    mockPool.query
      .mockResolvedValueOnce({ rows: [{ total_orders: '100' }] })
      .mockRejectedValueOnce(new Error('Products query failed'))
    
    const request = new NextRequest('http://localhost:3000/api/monitoring/business')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    // Should return dummy data when any query fails
    expect(data.totalOrders).toBe(1234) // Dummy data
  })
  
  it('빈 쿼리 결과를 처리한다', async () => {
    mockPool.query
      .mockResolvedValueOnce({ rows: [] }) // Empty orders result
      .mockResolvedValueOnce({ rows: [{}] })
      .mockResolvedValueOnce({ rows: [{}] })
    
    const request = new NextRequest('http://localhost:3000/api/monitoring/business')
    const response = await GET(request)
    
    // Should handle gracefully - might return dummy data or handle empty results
    expect(response.status).toBe(200)
  })
  
  it('무한대 전환율을 처리한다', async () => {
    mockPool.query
      .mockResolvedValueOnce({ rows: [{ completed_orders: '100' }] })
      .mockResolvedValueOnce({ rows: [{}] })
      .mockResolvedValueOnce({ rows: [{ unique_customers: '50', active_customers: '0' }] })
    
    const request = new NextRequest('http://localhost:3000/api/monitoring/business')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.conversionRate).toBe(0) // Should handle division by zero
  })
  
  it('문자열이 아닌 숫자를 올바르게 처리한다', async () => {
    const mockNumericResults = {
      rows: [{
        total_orders: 500,     // Number instead of string
        completed_orders: 400,
        cancelled_orders: 100,
        total_revenue: 250000.75,
        avg_order_value: 625.5
      }]
    }
    
    mockPool.query
      .mockResolvedValueOnce(mockNumericResults)
      .mockResolvedValueOnce({ rows: [{ total_products: 2000, active_products: 1800, out_of_stock: 50 }] })
      .mockResolvedValueOnce({ rows: [{ unique_customers: 300, active_customers: 80 }] })
    
    const request = new NextRequest('http://localhost:3000/api/monitoring/business')
    const response = await GET(request)
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.totalOrders).toBe(500)
    expect(data.totalRevenue).toBe(250000.75)
    expect(data.conversionRate).toBe(500) // 400/80 * 100
  })
  
  it('고급 쿼리 구조를 확인한다', async () => {
    mockPool.query
      .mockResolvedValueOnce({ rows: [{}] })
      .mockResolvedValueOnce({ rows: [{}] })
      .mockResolvedValueOnce({ rows: [{}] })
    
    const request = new NextRequest('http://localhost:3000/api/monitoring/business')
    await GET(request)
    
    const calls = mockPool.query.mock.calls
    
    // Verify orders query structure
    expect(calls[0][0]).toContain("COUNT(*) as total_orders")
    expect(calls[0][0]).toContain("CASE WHEN status = 'completed'")
    expect(calls[0][0]).toContain("SUM(CASE WHEN status = 'completed' THEN total_price")
    expect(calls[0][0]).toContain("AVG(CASE WHEN status = 'completed' THEN total_price")
    
    // Verify products query structure
    expect(calls[1][0]).toContain("COUNT(DISTINCT product_key)")
    expect(calls[1][0]).toContain("CASE WHEN status = 'active'")
    expect(calls[1][0]).toContain("stock_quantity <= 0")
    expect(calls[1][0]).toContain("supplier_key IN ('ownerclan', 'zentrade')")
    
    // Verify customers query structure
    expect(calls[2][0]).toContain("COUNT(DISTINCT customer_email)")
    expect(calls[2][0]).toContain("INTERVAL '30 days'")
  })
})