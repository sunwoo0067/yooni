import { GET } from '../route'
import { NextRequest } from 'next/server'
import { query } from '@/lib/db'

// Mock the database module
jest.mock('@/lib/db', () => ({
  query: jest.fn()
}))

describe('/api/orders', () => {
  const mockQuery = query as jest.MockedFunction<typeof query>
  
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  describe('GET', () => {
    it('기본 주문 목록을 반환한다', async () => {
      // Mock count query
      mockQuery.mockResolvedValueOnce([{ count: '25' }])
      
      // Mock orders query
      const mockOrders = [
        {
          id: 1,
          order_number: 'ORD001',
          supplier_id: 1,
          status: 'pending',
          total_amount: 50000,
          shipping_fee: 3000,
          customer_name: '홍길동',
          customer_phone: '010-1234-5678',
          customer_email: 'test@example.com',
          shipping_address: '서울시 강남구',
          shipping_postcode: '12345',
          created_at: new Date('2024-01-15'),
          updated_at: new Date('2024-01-15'),
          item_count: '3',
          total_quantity: '5'
        },
        {
          id: 2,
          order_number: 'ORD002',
          supplier_id: 2,
          status: 'processing',
          total_amount: 75000,
          shipping_fee: 0,
          customer_name: '김철수',
          customer_phone: '010-9876-5432',
          customer_email: 'kim@example.com',
          shipping_address: '부산시 해운대구',
          shipping_postcode: '67890',
          created_at: new Date('2024-01-14'),
          updated_at: new Date('2024-01-15'),
          item_count: '2',
          total_quantity: '2'
        }
      ]
      mockQuery.mockResolvedValueOnce(mockOrders)
      
      const request = new NextRequest('http://localhost:3000/api/orders')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.orders).toHaveLength(2)
      expect(data.orders[0].order_number).toBe('ORD001')
      expect(data.pagination).toEqual({
        page: 1,
        limit: 20,
        total: 25,
        totalPages: 2
      })
      
      // Verify query calls
      expect(mockQuery).toHaveBeenCalledTimes(2)
      expect(mockQuery).toHaveBeenNthCalledWith(
        1,
        'SELECT COUNT(*) FROM orders WHERE 1=1',
        []
      )
      expect(mockQuery).toHaveBeenNthCalledWith(
        2,
        expect.stringContaining('LEFT JOIN order_items'),
        [20, 0]
      )
    })
    
    it('검색 필터를 적용하여 주문을 조회한다', async () => {
      mockQuery.mockResolvedValueOnce([{ count: '3' }])
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest('http://localhost:3000/api/orders?search=홍길동&status=pending')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      
      // Verify search conditions
      expect(mockQuery).toHaveBeenNthCalledWith(
        1,
        expect.stringContaining('order_number ILIKE $1 OR customer_name ILIKE $1 OR customer_phone ILIKE $1'),
        ['%홍길동%', 'pending']
      )
    })
    
    it('날짜 범위 필터를 처리한다', async () => {
      mockQuery.mockResolvedValueOnce([{ count: '10' }])
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest('http://localhost:3000/api/orders?startDate=2024-01-01&endDate=2024-01-31')
      const response = await GET(request)
      
      expect(response.status).toBe(200)
      
      // Verify date range conditions
      const countQuery = mockQuery.mock.calls[0][0]
      expect(countQuery).toContain('created_at >= $1')
      expect(countQuery).toContain('created_at <= $2')
      
      // Verify endDate includes time
      expect(mockQuery).toHaveBeenNthCalledWith(
        1,
        expect.any(String),
        ['2024-01-01', '2024-01-31 23:59:59']
      )
    })
    
    it('공급사 필터를 처리한다', async () => {
      mockQuery.mockResolvedValueOnce([{ count: '15' }])
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest('http://localhost:3000/api/orders?supplier=3')
      const response = await GET(request)
      
      expect(response.status).toBe(200)
      
      // Verify supplier condition
      expect(mockQuery).toHaveBeenNthCalledWith(
        1,
        expect.stringContaining('supplier_id = $1'),
        ['3']
      )
    })
    
    it('페이지네이션을 올바르게 처리한다', async () => {
      mockQuery.mockResolvedValueOnce([{ count: '100' }])
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest('http://localhost:3000/api/orders?page=5&limit=10')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.pagination).toEqual({
        page: 5,
        limit: 10,
        total: 100,
        totalPages: 10
      })
      
      // Verify OFFSET calculation
      expect(mockQuery).toHaveBeenNthCalledWith(
        2,
        expect.stringContaining('LIMIT $1 OFFSET $2'),
        [10, 40] // offset = (5-1) * 10
      )
    })
    
    it('복합 필터 조건을 처리한다', async () => {
      mockQuery.mockResolvedValueOnce([{ count: '5' }])
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest(
        'http://localhost:3000/api/orders?search=010&supplier=1&status=completed&startDate=2024-01-01&endDate=2024-01-15'
      )
      const response = await GET(request)
      
      expect(response.status).toBe(200)
      
      // Verify all conditions are applied
      const countQuery = mockQuery.mock.calls[0][0]
      expect(countQuery).toContain('order_number ILIKE $1 OR customer_name ILIKE $1 OR customer_phone ILIKE $1')
      expect(countQuery).toContain('supplier_id = $2')
      expect(countQuery).toContain('status = $3')
      expect(countQuery).toContain('created_at >= $4')
      expect(countQuery).toContain('created_at <= $5')
      
      // Verify parameters order
      expect(mockQuery).toHaveBeenNthCalledWith(
        1,
        expect.any(String),
        ['%010%', '1', 'completed', '2024-01-01', '2024-01-15 23:59:59']
      )
    })
    
    it('주문 아이템 집계를 포함한다', async () => {
      mockQuery.mockResolvedValueOnce([{ count: '1' }])
      
      const mockOrder = [{
        id: 1,
        order_number: 'ORD003',
        supplier_id: 1,
        status: 'pending',
        total_amount: 30000,
        shipping_fee: 2500,
        customer_name: '이영희',
        customer_phone: '010-5555-5555',
        customer_email: 'lee@example.com',
        shipping_address: '인천시 연수구',
        shipping_postcode: '22222',
        created_at: new Date('2024-01-16'),
        updated_at: new Date('2024-01-16'),
        item_count: '5',
        total_quantity: '10'
      }]
      mockQuery.mockResolvedValueOnce(mockOrder)
      
      const request = new NextRequest('http://localhost:3000/api/orders')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.orders[0].item_count).toBe('5')
      expect(data.orders[0].total_quantity).toBe('10')
      
      // Verify GROUP BY is included
      expect(mockQuery).toHaveBeenNthCalledWith(
        2,
        expect.stringContaining('GROUP BY o.id'),
        expect.any(Array)
      )
    })
    
    it('데이터베이스 오류를 처리한다', async () => {
      mockQuery.mockRejectedValueOnce(new Error('Database connection failed'))
      
      const request = new NextRequest('http://localhost:3000/api/orders')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to fetch orders')
    })
    
    it('빈 결과를 올바르게 처리한다', async () => {
      mockQuery.mockResolvedValueOnce([{ count: '0' }])
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest('http://localhost:3000/api/orders?status=cancelled')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.orders).toHaveLength(0)
      expect(data.pagination.total).toBe(0)
      expect(data.pagination.totalPages).toBe(0)
    })
  })
})