import { GET, PUT } from '../route'
import { NextRequest } from 'next/server'
import { query } from '@/lib/db'

// Mock the database module
jest.mock('@/lib/db', () => ({
  query: jest.fn()
}))

describe('/api/stock/alerts', () => {
  const mockQuery = query as jest.MockedFunction<typeof query>
  
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  describe('GET', () => {
    it('모든 재고 알림을 반환한다', async () => {
      const mockAlerts = [
        {
          id: 1,
          product_id: 10,
          alert_type: 'out_of_stock',
          message: '테스트 상품 1이 품절되었습니다.',
          is_read: false,
          created_at: new Date('2024-01-15T10:00:00Z'),
          product_name: '테스트 상품 1',
          product_key: 'PROD001',
          supplier_name: 'OwnerClan'
        },
        {
          id: 2,
          product_id: 20,
          alert_type: 'low_stock',
          message: '테스트 상품 2의 재고가 부족합니다. (남은 수량: 3)',
          is_read: true,
          created_at: new Date('2024-01-15T09:30:00Z'),
          product_name: '테스트 상품 2',
          product_key: 'PROD002',
          supplier_name: 'ZenTrade'
        },
        {
          id: 3,
          product_id: 30,
          alert_type: 'back_in_stock',
          message: '테스트 상품 3이 재입고되었습니다.',
          is_read: false,
          created_at: new Date('2024-01-15T09:00:00Z'),
          product_name: '테스트 상품 3',
          product_key: 'PROD003',
          supplier_name: 'OwnerClan'
        }
      ]
      
      const mockUnreadCount = [{ count: '2' }]
      
      mockQuery.mockResolvedValueOnce(mockAlerts)
      mockQuery.mockResolvedValueOnce(mockUnreadCount)
      
      const request = new NextRequest('http://localhost:3000/api/stock/alerts')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.alerts).toHaveLength(3)
      expect(data.alerts[0].alert_type).toBe('out_of_stock')
      expect(data.alerts[1].alert_type).toBe('low_stock')
      expect(data.alerts[2].alert_type).toBe('back_in_stock')
      expect(data.unreadCount).toBe(2)
      
      // Verify queries
      expect(mockQuery).toHaveBeenCalledTimes(2)
      expect(mockQuery).toHaveBeenNthCalledWith(
        1,
        expect.stringContaining('JOIN products p ON a.product_id = p.id')
      )
      expect(mockQuery).toHaveBeenNthCalledWith(
        1,
        expect.stringContaining('JOIN suppliers s ON p.supplier_id = s.id')
      )
      expect(mockQuery).toHaveBeenNthCalledWith(
        1,
        expect.stringContaining('ORDER BY a.created_at DESC LIMIT 50')
      )
      expect(mockQuery).toHaveBeenNthCalledWith(
        2,
        'SELECT COUNT(*) as count FROM stock_alerts WHERE is_read = false'
      )
    })
    
    it('읽지 않은 알림만 반환한다', async () => {
      const mockUnreadAlerts = [
        {
          id: 1,
          product_id: 10,
          alert_type: 'out_of_stock',
          message: '품절 알림',
          is_read: false,
          created_at: new Date('2024-01-15T10:00:00Z'),
          product_name: '품절 상품',
          product_key: 'OUT001',
          supplier_name: 'TestSupplier'
        },
        {
          id: 3,
          product_id: 30,
          alert_type: 'low_stock',
          message: '저재고 알림',
          is_read: false,
          created_at: new Date('2024-01-15T09:00:00Z'),
          product_name: '저재고 상품',
          product_key: 'LOW001',
          supplier_name: 'TestSupplier'
        }
      ]
      
      const mockUnreadCount = [{ count: '2' }]
      
      mockQuery.mockResolvedValueOnce(mockUnreadAlerts)
      mockQuery.mockResolvedValueOnce(mockUnreadCount)
      
      const request = new NextRequest('http://localhost:3000/api/stock/alerts?unread=true')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.alerts).toHaveLength(2)
      expect(data.alerts.every(alert => !alert.is_read)).toBe(true)
      expect(data.unreadCount).toBe(2)
      
      // Verify unread filter
      expect(mockQuery).toHaveBeenNthCalledWith(
        1,
        expect.stringContaining('WHERE a.is_read = false')
      )
    })
    
    it('읽지 않은 알림이 없을 때 0을 반환한다', async () => {
      const mockEmptyAlerts = []
      const mockZeroCount = [{ count: '0' }]
      
      mockQuery.mockResolvedValueOnce(mockEmptyAlerts)
      mockQuery.mockResolvedValueOnce(mockZeroCount)
      
      const request = new NextRequest('http://localhost:3000/api/stock/alerts?unread=true')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.alerts).toHaveLength(0)
      expect(data.unreadCount).toBe(0)
    })
    
    it('COUNT 결과가 null일 때 0으로 처리한다', async () => {
      const mockAlerts = []
      const mockNullCount = [{}] // count 속성이 없는 경우
      
      mockQuery.mockResolvedValueOnce(mockAlerts)
      mockQuery.mockResolvedValueOnce(mockNullCount)
      
      const request = new NextRequest('http://localhost:3000/api/stock/alerts')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.unreadCount).toBe(0)
    })
    
    it('다양한 알림 유형을 처리한다', async () => {
      const mockVariousAlerts = [
        {
          id: 4,
          product_id: 40,
          alert_type: 'critical_low',
          message: '긴급 저재고 상황',
          is_read: false,
          created_at: new Date('2024-01-15T11:00:00Z'),
          product_name: '긴급 상품',
          product_key: 'CRIT001',
          supplier_name: 'Emergency Supplier'
        },
        {
          id: 5,
          product_id: 50,
          alert_type: 'discontinued',
          message: '상품이 단종되었습니다',
          is_read: false,
          created_at: new Date('2024-01-15T10:30:00Z'),
          product_name: '단종 상품',
          product_key: 'DISC001',
          supplier_name: 'Legacy Supplier'
        }
      ]
      
      const mockUnreadCount = [{ count: '2' }]
      
      mockQuery.mockResolvedValueOnce(mockVariousAlerts)
      mockQuery.mockResolvedValueOnce(mockUnreadCount)
      
      const request = new NextRequest('http://localhost:3000/api/stock/alerts')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.alerts[0].alert_type).toBe('critical_low')
      expect(data.alerts[1].alert_type).toBe('discontinued')
      expect(data.alerts.every(alert => !alert.is_read)).toBe(true)
    })
    
    it('데이터베이스 오류를 처리한다', async () => {
      mockQuery.mockRejectedValueOnce(new Error('Database connection failed'))
      
      const request = new NextRequest('http://localhost:3000/api/stock/alerts')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to fetch alerts')
    })
    
    it('unread 파라미터가 false일 때 모든 알림을 반환한다', async () => {
      const mockAllAlerts = [
        {
          id: 1,
          product_id: 10,
          alert_type: 'out_of_stock',
          message: '읽지 않은 알림',
          is_read: false,
          created_at: new Date('2024-01-15T10:00:00Z'),
          product_name: '상품 1',
          product_key: 'PROD001',
          supplier_name: 'Supplier1'
        },
        {
          id: 2,
          product_id: 20,
          alert_type: 'low_stock',
          message: '읽은 알림',
          is_read: true,
          created_at: new Date('2024-01-15T09:00:00Z'),
          product_name: '상품 2',
          product_key: 'PROD002',
          supplier_name: 'Supplier2'
        }
      ]
      
      const mockUnreadCount = [{ count: '1' }]
      
      mockQuery.mockResolvedValueOnce(mockAllAlerts)
      mockQuery.mockResolvedValueOnce(mockUnreadCount)
      
      const request = new NextRequest('http://localhost:3000/api/stock/alerts?unread=false')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.alerts).toHaveLength(2)
      expect(data.alerts[0].is_read).toBe(false)
      expect(data.alerts[1].is_read).toBe(true)
      
      // Verify no WHERE clause for unread filter
      expect(mockQuery).toHaveBeenNthCalledWith(
        1,
        expect.not.stringContaining('WHERE a.is_read = false')
      )
    })
  })
  
  describe('PUT', () => {
    const createRequest = (body: any) => {
      return new NextRequest('http://localhost:3000/api/stock/alerts', {
        method: 'PUT',
        body: JSON.stringify(body)
      })
    }
    
    it('선택된 알림들을 읽음 처리한다', async () => {
      const alertIds = [1, 3, 5]
      
      mockQuery.mockResolvedValueOnce(undefined)
      
      const request = createRequest({ alertIds })
      const response = await PUT(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      
      // Verify UPDATE query
      expect(mockQuery).toHaveBeenCalledWith(
        'UPDATE stock_alerts SET is_read = true WHERE id = ANY($1)',
        [[1, 3, 5]]
      )
    })
    
    it('단일 알림을 읽음 처리한다', async () => {
      const alertIds = [7]
      
      mockQuery.mockResolvedValueOnce(undefined)
      
      const request = createRequest({ alertIds })
      const response = await PUT(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      
      expect(mockQuery).toHaveBeenCalledWith(
        'UPDATE stock_alerts SET is_read = true WHERE id = ANY($1)',
        [[7]]
      )
    })
    
    it('빈 배열일 때 쿼리를 실행하지 않는다', async () => {
      const alertIds = []
      
      const request = createRequest({ alertIds })
      const response = await PUT(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      
      // Verify no query was executed
      expect(mockQuery).not.toHaveBeenCalled()
    })
    
    it('alertIds가 없을 때 쿼리를 실행하지 않는다', async () => {
      const request = createRequest({})
      const response = await PUT(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      
      expect(mockQuery).not.toHaveBeenCalled()
    })
    
    it('alertIds가 null일 때 쿼리를 실행하지 않는다', async () => {
      const request = createRequest({ alertIds: null })
      const response = await PUT(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      
      expect(mockQuery).not.toHaveBeenCalled()
    })
    
    it('대량의 알림 ID를 처리한다', async () => {
      const alertIds = Array.from({ length: 100 }, (_, i) => i + 1)
      
      mockQuery.mockResolvedValueOnce(undefined)
      
      const request = createRequest({ alertIds })
      const response = await PUT(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      
      expect(mockQuery).toHaveBeenCalledWith(
        'UPDATE stock_alerts SET is_read = true WHERE id = ANY($1)',
        [alertIds]
      )
    })
    
    it('데이터베이스 오류를 처리한다', async () => {
      const alertIds = [1, 2, 3]
      
      mockQuery.mockRejectedValueOnce(new Error('Update failed'))
      
      const request = createRequest({ alertIds })
      const response = await PUT(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to update alerts')
    })
    
    it('잘못된 JSON 형식을 처리한다', async () => {
      const request = new NextRequest('http://localhost:3000/api/stock/alerts', {
        method: 'PUT',
        body: 'invalid json'
      })
      
      const response = await PUT(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to update alerts')
    })
    
    it('문자열 ID 배열을 처리한다', async () => {
      const alertIds = ['1', '2', '3'] // 문자열 형태의 ID
      
      mockQuery.mockResolvedValueOnce(undefined)
      
      const request = createRequest({ alertIds })
      const response = await PUT(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      
      expect(mockQuery).toHaveBeenCalledWith(
        'UPDATE stock_alerts SET is_read = true WHERE id = ANY($1)',
        [['1', '2', '3']]
      )
    })
  })
})