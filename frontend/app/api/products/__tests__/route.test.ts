import { GET } from '../route'
import { NextRequest } from 'next/server'
import { query } from '@/lib/db'

// Mock the database module
jest.mock('@/lib/db', () => ({
  query: jest.fn()
}))

describe('/api/products', () => {
  const mockQuery = query as jest.MockedFunction<typeof query>
  
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  describe('GET', () => {
    it('기본 상품 목록을 반환한다', async () => {
      // Mock count query
      mockQuery.mockResolvedValueOnce([{ count: '50' }])
      
      // Mock products query
      const mockProducts = [
        {
          id: 1,
          raw_data_id: 1,
          supplier_id: 1,
          product_key: 'PROD001',
          name: '테스트 상품 1',
          price: 10000,
          status: 'active',
          stock_status: 'in_stock',
          stock_quantity: 100,
          last_stock_check: new Date('2024-01-15'),
          stock_sync_enabled: true,
          metadata: {},
          created_at: new Date('2024-01-01'),
          updated_at: new Date('2024-01-15')
        },
        {
          id: 2,
          raw_data_id: 2,
          supplier_id: 1,
          product_key: 'PROD002',
          name: '테스트 상품 2',
          price: 20000,
          status: 'active',
          stock_status: 'low_stock',
          stock_quantity: 5,
          last_stock_check: new Date('2024-01-15'),
          stock_sync_enabled: false,
          metadata: {},
          created_at: new Date('2024-01-02'),
          updated_at: new Date('2024-01-15')
        }
      ]
      mockQuery.mockResolvedValueOnce(mockProducts)
      
      const request = new NextRequest('http://localhost:3000/api/products')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.products).toHaveLength(2)
      expect(data.products[0].name).toBe('테스트 상품 1')
      expect(data.pagination).toEqual({
        page: 1,
        limit: 20,
        total: 50,
        totalPages: 3
      })
      
      // Verify query calls
      expect(mockQuery).toHaveBeenCalledTimes(2)
      expect(mockQuery).toHaveBeenNthCalledWith(
        1,
        'SELECT COUNT(*) FROM products WHERE 1=1',
        []
      )
    })
    
    it('검색 필터를 적용하여 상품을 조회한다', async () => {
      mockQuery.mockResolvedValueOnce([{ count: '5' }])
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest('http://localhost:3000/api/products?search=테스트&supplier=1&status=active')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      
      // Verify filter conditions
      expect(mockQuery).toHaveBeenNthCalledWith(
        1,
        expect.stringContaining('name ILIKE $1 OR product_key ILIKE $1'),
        ['%테스트%', '1', 'active']
      )
    })
    
    it('페이지네이션을 처리한다', async () => {
      mockQuery.mockResolvedValueOnce([{ count: '100' }])
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest('http://localhost:3000/api/products?page=3&limit=10')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.pagination).toEqual({
        page: 3,
        limit: 10,
        total: 100,
        totalPages: 10
      })
      
      // Verify LIMIT and OFFSET
      expect(mockQuery).toHaveBeenNthCalledWith(
        2,
        expect.stringContaining('LIMIT $1 OFFSET $2'),
        [10, 20] // offset = (page - 1) * limit = 2 * 10
      )
    })
    
    it('정렬 옵션을 처리한다', async () => {
      mockQuery.mockResolvedValueOnce([{ count: '10' }])
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest('http://localhost:3000/api/products?sortBy=price&sortOrder=ASC')
      const response = await GET(request)
      
      expect(response.status).toBe(200)
      expect(mockQuery).toHaveBeenNthCalledWith(
        2,
        expect.stringContaining('ORDER BY price ASC'),
        expect.any(Array)
      )
    })
    
    it('데이터베이스 오류를 처리한다', async () => {
      mockQuery.mockRejectedValueOnce(new Error('Database connection error'))
      
      const request = new NextRequest('http://localhost:3000/api/products')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to fetch products')
    })
    
    it('복합 필터 조건을 올바르게 처리한다', async () => {
      mockQuery.mockResolvedValueOnce([{ count: '2' }])
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest('http://localhost:3000/api/products?search=노트북&supplier=2&status=inactive&sortBy=updated_at')
      const response = await GET(request)
      
      expect(response.status).toBe(200)
      
      // Verify all conditions are included
      const countQuery = mockQuery.mock.calls[0][0]
      expect(countQuery).toContain('name ILIKE $1 OR product_key ILIKE $1')
      expect(countQuery).toContain('supplier_id = $2')
      expect(countQuery).toContain('status = $3')
      
      // Verify parameters
      expect(mockQuery).toHaveBeenNthCalledWith(
        1,
        expect.any(String),
        ['%노트북%', '2', 'inactive']
      )
    })
    
    it('빈 결과를 올바르게 처리한다', async () => {
      mockQuery.mockResolvedValueOnce([{ count: '0' }])
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest('http://localhost:3000/api/products?search=존재하지않는상품')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.products).toHaveLength(0)
      expect(data.pagination.total).toBe(0)
      expect(data.pagination.totalPages).toBe(0)
    })
    
    it('잘못된 페이지 번호를 기본값으로 처리한다', async () => {
      mockQuery.mockResolvedValueOnce([{ count: '10' }])
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest('http://localhost:3000/api/products?page=invalid&limit=abc')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.pagination.page).toBe(1)
      expect(data.pagination.limit).toBe(20)
    })
  })
})