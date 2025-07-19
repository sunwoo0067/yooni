import { GET } from '../route'
import { NextRequest } from 'next/server'
import { query } from '@/lib/db'

// Mock the database module
jest.mock('@/lib/db', () => ({
  query: jest.fn()
}))

describe('/api/collection-logs', () => {
  const mockQuery = query as jest.MockedFunction<typeof query>
  
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  describe('GET', () => {
    it('기본 컬렉션 로그 목록을 반환한다', async () => {
      const mockLogs = [
        {
          id: 1,
          supplier_id: 1,
          status: 'completed',
          total_products: 1500,
          new_products: 25,
          updated_products: 100,
          error_count: 2,
          started_at: new Date('2024-01-15T09:00:00Z'),
          completed_at: new Date('2024-01-15T09:15:00Z'),
          error_message: null,
          supplier_name: 'OwnerClan'
        },
        {
          id: 2,
          supplier_id: 2,
          status: 'running',
          total_products: 0,
          new_products: 0,
          updated_products: 0,
          error_count: 0,
          started_at: new Date('2024-01-15T10:00:00Z'),
          completed_at: null,
          error_message: null,
          supplier_name: 'ZenTrade'
        },
        {
          id: 3,
          supplier_id: 1,
          status: 'failed',
          total_products: 0,
          new_products: 0,
          updated_products: 0,
          error_count: 1,
          started_at: new Date('2024-01-15T08:00:00Z'),
          completed_at: new Date('2024-01-15T08:05:00Z'),
          error_message: 'API connection timeout',
          supplier_name: 'OwnerClan'
        }
      ]
      
      mockQuery.mockResolvedValueOnce(mockLogs)
      
      const request = new NextRequest('http://localhost:3000/api/collection-logs')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data).toHaveLength(3)
      expect(data[0].supplier_name).toBe('OwnerClan')
      expect(data[0].status).toBe('completed')
      expect(data[1].status).toBe('running')
      expect(data[2].status).toBe('failed')
      
      // Verify query structure
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('LEFT JOIN suppliers s ON cl.supplier_id = s.id'),
        [100] // default limit
      )
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('ORDER BY cl.started_at DESC'),
        expect.any(Array)
      )
    })
    
    it('공급사 필터를 적용한다', async () => {
      const mockFilteredLogs = [
        {
          id: 1,
          supplier_id: 1,
          status: 'completed',
          total_products: 1500,
          new_products: 25,
          updated_products: 100,
          error_count: 2,
          started_at: new Date('2024-01-15T09:00:00Z'),
          completed_at: new Date('2024-01-15T09:15:00Z'),
          error_message: null,
          supplier_name: 'OwnerClan'
        }
      ]
      
      mockQuery.mockResolvedValueOnce(mockFilteredLogs)
      
      const request = new NextRequest('http://localhost:3000/api/collection-logs?supplier=1')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data).toHaveLength(1)
      expect(data[0].supplier_id).toBe(1)
      
      // Verify supplier filter
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('cl.supplier_id = $1'),
        [1, 100]
      )
    })
    
    it('상태 필터를 적용한다', async () => {
      const mockStatusLogs = [
        {
          id: 4,
          supplier_id: 2,
          status: 'failed',
          total_products: 0,
          new_products: 0,
          updated_products: 0,
          error_count: 5,
          started_at: new Date('2024-01-15T07:00:00Z'),
          completed_at: new Date('2024-01-15T07:10:00Z'),
          error_message: 'Authentication failed',
          supplier_name: 'ZenTrade'
        }
      ]
      
      mockQuery.mockResolvedValueOnce(mockStatusLogs)
      
      const request = new NextRequest('http://localhost:3000/api/collection-logs?status=failed')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data).toHaveLength(1)
      expect(data[0].status).toBe('failed')
      expect(data[0].error_message).toBe('Authentication failed')
      
      // Verify status filter
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('cl.status = $1'),
        ['failed', 100]
      )
    })
    
    it('복합 필터를 처리한다', async () => {
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest('http://localhost:3000/api/collection-logs?supplier=2&status=running&limit=50')
      const response = await GET(request)
      
      expect(response.status).toBe(200)
      
      // Verify all filters are applied
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('cl.supplier_id = $1 AND cl.status = $2'),
        [2, 'running', 50]
      )
    })
    
    it('사용자 정의 limit을 처리한다', async () => {
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest('http://localhost:3000/api/collection-logs?limit=25')
      const response = await GET(request)
      
      expect(response.status).toBe(200)
      
      // Verify custom limit
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('LIMIT $1'),
        [25]
      )
    })
    
    it('잘못된 limit 값을 기본값으로 처리한다', async () => {
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest('http://localhost:3000/api/collection-logs?limit=invalid')
      const response = await GET(request)
      
      expect(response.status).toBe(200)
      
      // Verify default limit when invalid
      expect(mockQuery).toHaveBeenCalledWith(
        expect.any(String),
        [100] // default limit
      )
    })
    
    it('실행 중인 컬렉션 작업을 올바르게 표시한다', async () => {
      const runningLogs = [
        {
          id: 5,
          supplier_id: 3,
          status: 'running',
          total_products: 500,
          new_products: 10,
          updated_products: 50,
          error_count: 0,
          started_at: new Date('2024-01-15T11:00:00Z'),
          completed_at: null,
          error_message: null,
          supplier_name: 'TestSupplier'
        }
      ]
      
      mockQuery.mockResolvedValueOnce(runningLogs)
      
      const request = new NextRequest('http://localhost:3000/api/collection-logs?status=running')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data[0].status).toBe('running')
      expect(data[0].completed_at).toBeNull()
      expect(data[0].total_products).toBe(500)
      expect(data[0].error_count).toBe(0)
    })
    
    it('공급사명이 없는 로그를 처리한다', async () => {
      const orphanLogs = [
        {
          id: 6,
          supplier_id: 999, // non-existent supplier
          status: 'completed',
          total_products: 0,
          new_products: 0,
          updated_products: 0,
          error_count: 0,
          started_at: new Date('2024-01-15T06:00:00Z'),
          completed_at: new Date('2024-01-15T06:05:00Z'),
          error_message: null,
          supplier_name: null // LEFT JOIN result
        }
      ]
      
      mockQuery.mockResolvedValueOnce(orphanLogs)
      
      const request = new NextRequest('http://localhost:3000/api/collection-logs')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data[0].supplier_name).toBeNull()
      expect(data[0].supplier_id).toBe(999)
      
      // Verify LEFT JOIN handles missing suppliers
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringContaining('LEFT JOIN suppliers s'),
        expect.any(Array)
      )
    })
    
    it('빈 결과를 올바르게 처리한다', async () => {
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest('http://localhost:3000/api/collection-logs?supplier=999')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data).toHaveLength(0)
      expect(Array.isArray(data)).toBe(true)
    })
    
    it('데이터베이스 오류를 처리한다', async () => {
      mockQuery.mockRejectedValueOnce(new Error('Database connection failed'))
      
      const request = new NextRequest('http://localhost:3000/api/collection-logs')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to fetch collection logs')
    })
    
    it('매개변수 인덱싱이 올바르게 작동한다', async () => {
      mockQuery.mockResolvedValueOnce([])
      
      const request = new NextRequest('http://localhost:3000/api/collection-logs?supplier=1&status=completed&limit=10')
      const response = await GET(request)
      
      expect(response.status).toBe(200)
      
      // Verify parameter indexing and order
      expect(mockQuery).toHaveBeenCalledWith(
        expect.stringMatching(/\$1.*\$2.*\$3/),
        [1, 'completed', 10]
      )
    })
    
    it('다양한 로그 상태들을 처리한다', async () => {
      const mixedStatusLogs = [
        {
          id: 7,
          supplier_id: 1,
          status: 'pending',
          total_products: 0,
          new_products: 0,
          updated_products: 0,
          error_count: 0,
          started_at: new Date('2024-01-15T12:00:00Z'),
          completed_at: null,
          error_message: null,
          supplier_name: 'OwnerClan'
        },
        {
          id: 8,
          supplier_id: 1,
          status: 'cancelled',
          total_products: 250,
          new_products: 5,
          updated_products: 20,
          error_count: 0,
          started_at: new Date('2024-01-15T11:30:00Z'),
          completed_at: new Date('2024-01-15T11:35:00Z'),
          error_message: 'Cancelled by user',
          supplier_name: 'OwnerClan'
        }
      ]
      
      mockQuery.mockResolvedValueOnce(mixedStatusLogs)
      
      const request = new NextRequest('http://localhost:3000/api/collection-logs')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data).toHaveLength(2)
      expect(data[0].status).toBe('pending')
      expect(data[1].status).toBe('cancelled')
      expect(data[1].error_message).toBe('Cancelled by user')
    })
  })
})