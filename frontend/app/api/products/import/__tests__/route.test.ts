import { POST } from '../route'
import { NextRequest } from 'next/server'
import { query, getOne } from '@/lib/db'

// Mock the database module
jest.mock('@/lib/db', () => ({
  query: jest.fn(),
  getOne: jest.fn()
}))

describe('/api/products/import', () => {
  const mockQuery = query as jest.MockedFunction<typeof query>
  const mockGetOne = getOne as jest.MockedFunction<typeof getOne>
  
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  describe('POST', () => {
    const createRequest = (body: any) => {
      return new NextRequest('http://localhost:3000/api/products/import', {
        method: 'POST',
        body: JSON.stringify(body)
      })
    }
    
    it('새 상품을 성공적으로 생성한다', async () => {
      const productData = {
        supplierId: 1,
        productData: {
          product_key: 'NEW001',
          name: '새 상품',
          price: 15000,
          status: 'active',
          stock_status: 'in_stock',
          stock_quantity: 50,
          metadata: { brand: 'TestBrand' }
        }
      }
      
      // Mock no existing product
      mockGetOne.mockResolvedValueOnce(null)
      
      // Mock insert result
      mockGetOne.mockResolvedValueOnce({ id: 100 })
      
      const request = createRequest(productData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data).toEqual({
        success: true,
        action: 'created',
        productId: 100
      })
      
      // Verify database calls
      expect(mockGetOne).toHaveBeenCalledWith(
        expect.stringContaining('SELECT id FROM products WHERE'),
        [1, 'NEW001']
      )
      expect(mockGetOne).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO products'),
        expect.arrayContaining(['NEW001', '새 상품', 15000])
      )
    })
    
    it('기존 상품을 성공적으로 업데이트한다', async () => {
      const productData = {
        supplierId: 1,
        productData: {
          product_key: 'EXIST001',
          name: '업데이트된 상품',
          price: 20000,
          status: 'active',
          stock_status: 'in_stock',
          stock_quantity: 100,
          metadata: { updated: true }
        }
      }
      
      // Mock existing product
      mockGetOne.mockResolvedValueOnce({ id: 50 })
      
      // Mock current product status
      mockGetOne.mockResolvedValueOnce({ 
        status: 'active',
        stock_status: 'low_stock',
        stock_quantity: 5
      })
      
      const request = createRequest(productData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data).toEqual({
        success: true,
        action: 'updated',
        productId: 50
      })
      
      // Verify update query
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('UPDATE products'),
        expect.arrayContaining(['업데이트된 상품', 20000, 'active'])
      )
    })
    
    it('품절 상태 변경 시 알림을 생성한다', async () => {
      const productData = {
        supplierId: 1,
        productData: {
          product_key: 'STOCK001',
          name: '재고 테스트 상품',
          price: 10000,
          status: 'active',
          stock_status: 'out_of_stock',
          stock_quantity: 0,
          metadata: {}
        }
      }
      
      // Mock existing product
      mockGetOne.mockResolvedValueOnce({ id: 30 })
      
      // Mock current product with in_stock status
      mockGetOne.mockResolvedValueOnce({ 
        status: 'active',
        stock_status: 'in_stock',
        stock_quantity: 50
      })
      
      const request = createRequest(productData)
      const response = await POST(request)
      
      expect(response.status).toBe(200)
      
      // Verify alert creation
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO stock_alerts'),
        [30, 'out_of_stock', expect.stringContaining('품절되었습니다')]
      )
      
      // Verify stock history
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO stock_history'),
        expect.arrayContaining([30, 'in_stock', 'out_of_stock'])
      )
    })
    
    it('재입고 시 알림을 생성한다', async () => {
      const productData = {
        supplierId: 1,
        productData: {
          product_key: 'RESTOCK001',
          name: '재입고 상품',
          price: 25000,
          status: 'active',
          stock_status: 'in_stock',
          stock_quantity: 100,
          metadata: {}
        }
      }
      
      // Mock existing product
      mockGetOne.mockResolvedValueOnce({ id: 40 })
      
      // Mock current product with out_of_stock status
      mockGetOne.mockResolvedValueOnce({ 
        status: 'active',
        stock_status: 'out_of_stock',
        stock_quantity: 0
      })
      
      const request = createRequest(productData)
      const response = await POST(request)
      
      expect(response.status).toBe(200)
      
      // Verify back in stock alert
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO stock_alerts'),
        [40, 'back_in_stock', expect.stringContaining('재입고되었습니다')]
      )
    })
    
    it('새 상품이 품절 상태로 등록될 때 알림을 생성한다', async () => {
      const productData = {
        supplierId: 2,
        productData: {
          product_key: 'NEWOUT001',
          name: '품절 신상품',
          price: 30000,
          status: 'active',
          stock_status: 'out_of_stock',
          stock_quantity: 0,
          metadata: {}
        }
      }
      
      // Mock no existing product
      mockGetOne.mockResolvedValueOnce(null)
      
      // Mock insert result
      mockGetOne.mockResolvedValueOnce({ id: 200 })
      
      const request = createRequest(productData)
      const response = await POST(request)
      
      expect(response.status).toBe(200)
      
      // Verify out of stock alert for new product
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO stock_alerts'),
        [200, expect.stringContaining('품절 상태로 등록')]
      )
    })
    
    it('필수 데이터가 없을 때 오류를 반환한다', async () => {
      const request = createRequest({
        supplierId: 1,
        productData: {} // Missing required fields
      })
      
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to import product')
    })
    
    it('데이터베이스 오류를 처리한다', async () => {
      const productData = {
        supplierId: 1,
        productData: {
          product_key: 'ERROR001',
          name: '오류 테스트',
          price: 10000,
          status: 'active'
        }
      }
      
      // Mock database error
      mockGetOne.mockRejectedValueOnce(new Error('Database error'))
      
      const request = createRequest(productData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to import product')
    })
    
    it('메타데이터를 올바르게 JSON 문자열로 변환한다', async () => {
      const productData = {
        supplierId: 1,
        productData: {
          product_key: 'META001',
          name: '메타데이터 테스트',
          price: 15000,
          status: 'active',
          metadata: {
            brand: 'TestBrand',
            category: ['Electronics', 'Mobile'],
            specifications: {
              weight: '150g',
              dimensions: '10x5x2cm'
            }
          }
        }
      }
      
      mockGetOne.mockResolvedValueOnce(null)
      mockGetOne.mockResolvedValueOnce({ id: 300 })
      
      const request = createRequest(productData)
      await POST(request)
      
      // Verify metadata is stringified
      expect(mockGetOne).toHaveBeenCalledWith(
        expect.any(String),
        expect.arrayContaining([
          JSON.stringify(productData.productData.metadata)
        ])
      )
    })
  })
})