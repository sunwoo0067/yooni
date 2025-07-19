import { GET, POST } from '../route'
import { NextRequest } from 'next/server'
import { query, getOne } from '@/lib/db'

// Mock the database module
jest.mock('@/lib/db', () => ({
  query: jest.fn(),
  getOne: jest.fn()
}))

describe('/api/suppliers', () => {
  const mockQuery = query as jest.MockedFunction<typeof query>
  const mockGetOne = getOne as jest.MockedFunction<typeof getOne>
  
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  describe('GET', () => {
    it('공급사 목록과 상품 통계를 반환한다', async () => {
      const mockSuppliers = [
        {
          id: 1,
          name: '테스트 공급사 1',
          contact_info: 'test1@example.com',
          business_number: '123-45-67890',
          address: '서울시 강남구',
          created_at: new Date('2024-01-01'),
          updated_at: new Date('2024-01-15'),
          product_count: 25,
          active_products: 20,
          last_product_update: new Date('2024-01-14')
        },
        {
          id: 2,
          name: '테스트 공급사 2',
          contact_info: 'test2@example.com',
          business_number: '987-65-43210',
          address: '부산시 해운대구',
          created_at: new Date('2024-01-02'),
          updated_at: new Date('2024-01-15'),
          product_count: 15,
          active_products: 10,
          last_product_update: new Date('2024-01-13')
        },
        {
          id: 3,
          name: '신규 공급사',
          contact_info: 'new@example.com',
          business_number: '555-55-55555',
          address: '대구시 중구',
          created_at: new Date('2024-01-15'),
          updated_at: new Date('2024-01-15'),
          product_count: 0,
          active_products: 0,
          last_product_update: null
        }
      ]
      
      mockQuery.mockResolvedValueOnce(mockSuppliers)
      
      const request = new NextRequest('http://localhost:3000/api/suppliers')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data).toHaveLength(3)
      expect(data[0].name).toBe('테스트 공급사 1')
      expect(data[0].product_count).toBe(25)
      expect(data[0].active_products).toBe(20)
      expect(data[2].product_count).toBe(0) // 신규 공급사
      
      // Verify complex query structure
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('LEFT JOIN')
      )
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('COALESCE(stats.product_count, 0)')
      )
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('GROUP BY supplier_id')
      )
    })
    
    it('공급사가 없을 때 빈 배열을 반환한다', async () => {
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest('http://localhost:3000/api/suppliers')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data).toHaveLength(0)
      expect(Array.isArray(data)).toBe(true)
    })
    
    it('데이터베이스 오류를 처리한다', async () => {
      mockQuery.mockRejectedValueOnce(new Error('Database connection failed'))
      
      const request = new NextRequest('http://localhost:3000/api/suppliers')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to fetch suppliers')
    })
    
    it('상품 통계가 올바르게 집계된다', async () => {
      const mockSuppliersWithStats = [
        {
          id: 1,
          name: '활성 공급사',
          contact_info: 'active@example.com',
          business_number: '111-11-11111',
          address: '서울시 종로구',
          created_at: new Date('2024-01-01'),
          updated_at: new Date('2024-01-15'),
          product_count: 100,
          active_products: 85,
          last_product_update: new Date('2024-01-15')
        }
      ]
      
      mockQuery.mockResolvedValueOnce(mockSuppliersWithStats)
      
      const request = new NextRequest('http://localhost:3000/api/suppliers')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data[0].product_count).toBe(100)
      expect(data[0].active_products).toBe(85)
      expect(data[0].last_product_update).toBeTruthy()
      
      // Verify aggregation logic in query
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining("COUNT(CASE WHEN status = 'active' THEN 1 END)")
      )
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('MAX(updated_at) as last_product_update')
      )
    })
  })
  
  describe('POST', () => {
    const createRequest = (body: any) => {
      return new NextRequest('http://localhost:3000/api/suppliers', {
        method: 'POST',
        body: JSON.stringify(body)
      })
    }
    
    it('새 공급사를 성공적으로 생성한다', async () => {
      const supplierData = {
        name: '새로운 공급사',
        contact_info: 'new@supplier.com',
        business_number: '333-33-33333',
        address: '인천시 연수구 테스트동 123'
      }
      
      // Mock no existing supplier
      mockGetOne.mockResolvedValueOnce(null)
      
      // Mock insert result
      const createdSupplier = {
        id: 10,
        ...supplierData,
        created_at: new Date('2024-01-16'),
        updated_at: new Date('2024-01-16')
      }
      mockGetOne.mockResolvedValueOnce(createdSupplier)
      
      const request = createRequest(supplierData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.id).toBe(10)
      expect(data.name).toBe('새로운 공급사')
      expect(data.contact_info).toBe('new@supplier.com')
      
      // Verify duplicate check
      expect(mockGetOne).toHaveBeenNthCalledWith(
        1,
        'SELECT id FROM suppliers WHERE name = $1',
        ['새로운 공급사']
      )
      
      // Verify insert query
      expect(mockGetOne).toHaveBeenNthCalledWith(
        2,
        expect.stringContaining('INSERT INTO suppliers'),
        [
          '새로운 공급사',
          'new@supplier.com',
          '333-33-33333',
          '인천시 연수구 테스트동 123'
        ]
      )
    })
    
    it('중복된 공급사명에 대해 오류를 반환한다', async () => {
      const supplierData = {
        name: '기존 공급사',
        contact_info: 'existing@supplier.com',
        business_number: '444-44-44444',
        address: '대전시 유성구'
      }
      
      // Mock existing supplier
      mockGetOne.mockResolvedValueOnce({ id: 5 })
      
      const request = createRequest(supplierData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(400)
      expect(data.error).toBe('이미 존재하는 공급사명입니다.')
      
      // Verify only duplicate check was called
      expect(mockGetOne).toHaveBeenCalledTimes(1)
      expect(mockGetOne).toHaveBeenCalledWith(
        'SELECT id FROM suppliers WHERE name = $1',
        ['기존 공급사']
      )
    })
    
    it('필수 필드만으로 공급사를 생성한다', async () => {
      const minimalData = {
        name: '최소 정보 공급사'
      }
      
      mockGetOne.mockResolvedValueOnce(null)
      mockGetOne.mockResolvedValueOnce({
        id: 20,
        name: '최소 정보 공급사',
        contact_info: '',
        business_number: '',
        address: '',
        created_at: new Date(),
        updated_at: new Date()
      })
      
      const request = createRequest(minimalData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.name).toBe('최소 정보 공급사')
      
      // Verify empty strings for optional fields
      expect(mockGetOne).toHaveBeenNthCalledWith(
        2,
        expect.stringContaining('INSERT INTO suppliers'),
        ['최소 정보 공급사', '', '', '']
      )
    })
    
    it('선택적 필드를 올바르게 처리한다', async () => {
      const partialData = {
        name: '부분 정보 공급사',
        contact_info: 'partial@example.com',
        business_number: '777-77-77777'
        // address는 누락
      }
      
      mockGetOne.mockResolvedValueOnce(null)
      mockGetOne.mockResolvedValueOnce({
        id: 30,
        ...partialData,
        address: '',
        created_at: new Date(),
        updated_at: new Date()
      })
      
      const request = createRequest(partialData)
      const response = await POST(request)
      
      expect(response.status).toBe(200)
      
      // Verify optional fields default to empty string
      expect(mockGetOne).toHaveBeenNthCalledWith(
        2,
        expect.any(String),
        [
          '부분 정보 공급사',
          'partial@example.com',
          '777-77-77777',
          '' // address defaults to empty
        ]
      )
    })
    
    it('공급사명이 없을 때도 정상 처리한다 (빈 문자열로)', async () => {
      const invalidData = {
        contact_info: 'invalid@example.com'
        // name is missing (undefined becomes '')
      }
      
      mockGetOne.mockResolvedValueOnce(null) // No existing supplier with empty name
      mockGetOne.mockResolvedValueOnce({
        id: 999,
        name: '',
        contact_info: 'invalid@example.com',
        business_number: '',
        address: '',
        created_at: new Date(),
        updated_at: new Date()
      })
      
      const request = createRequest(invalidData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.name).toBe('') // Empty string when name is undefined
    })
    
    it('데이터베이스 연결 오류를 처리한다', async () => {
      const supplierData = {
        name: '오류 테스트 공급사'
      }
      
      // Mock database error on duplicate check
      mockGetOne.mockRejectedValueOnce(new Error('Database connection error'))
      
      const request = createRequest(supplierData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to create supplier')
    })
    
    it('생성 중 데이터베이스 오류를 처리한다', async () => {
      const supplierData = {
        name: '생성 오류 테스트'
      }
      
      // Mock successful duplicate check
      mockGetOne.mockResolvedValueOnce(null)
      
      // Mock error during insert
      mockGetOne.mockRejectedValueOnce(new Error('Insert failed'))
      
      const request = createRequest(supplierData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to create supplier')
    })
    
    it('완전한 공급사 정보로 생성한다', async () => {
      const completeData = {
        name: '완전한 공급사',
        contact_info: 'complete@supplier.com, 02-1234-5678',
        business_number: '999-99-99999',
        address: '서울특별시 강남구 테헤란로 123, 456호'
      }
      
      mockGetOne.mockResolvedValueOnce(null)
      mockGetOne.mockResolvedValueOnce({
        id: 100,
        ...completeData,
        created_at: new Date('2024-01-16'),
        updated_at: new Date('2024-01-16')
      })
      
      const request = createRequest(completeData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data).toEqual(expect.objectContaining({
        id: 100,
        name: '완전한 공급사',
        contact_info: 'complete@supplier.com, 02-1234-5678',
        business_number: '999-99-99999',
        address: '서울특별시 강남구 테헤란로 123, 456호'
      }))
      
      // Verify all fields are properly passed
      expect(mockGetOne).toHaveBeenNthCalledWith(
        2,
        expect.stringContaining('RETURNING *'),
        [
          '완전한 공급사',
          'complete@supplier.com, 02-1234-5678',
          '999-99-99999',
          '서울특별시 강남구 테헤란로 123, 456호'
        ]
      )
    })
  })
})