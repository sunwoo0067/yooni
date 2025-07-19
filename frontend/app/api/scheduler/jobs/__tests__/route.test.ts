import { GET, POST } from '../route'
import { NextRequest } from 'next/server'

// Mock the pg pool
const mockPool = {
  query: jest.fn()
}

jest.mock('pg', () => ({
  Pool: jest.fn().mockImplementation(() => mockPool)
}))

describe('/api/scheduler/jobs', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  describe('GET', () => {
    it('활성 스케줄 작업 목록을 반환한다', async () => {
      const mockJobs = [
        {
          id: 1,
          name: '상품 수집',
          job_type: 'collection',
          status: 'active',
          interval: 'daily',
          specific_times: ['09:00', '18:00'],
          market_codes: ['ownerclan', 'zentrade'],
          next_run_at: new Date('2024-01-16T09:00:00Z'),
          last_run_at: new Date('2024-01-15T18:00:00Z'),
          last_success_at: new Date('2024-01-15T18:05:00Z'),
          run_count: 50,
          success_count: 48,
          error_count: 2,
          last_error: null,
          success_rate: 96.00
        },
        {
          id: 2,
          name: '재고 동기화',
          job_type: 'stock_sync',
          status: 'active',
          interval: 'hourly',
          specific_times: null,
          market_codes: ['coupang'],
          next_run_at: new Date('2024-01-15T20:00:00Z'),
          last_run_at: new Date('2024-01-15T19:00:00Z'),
          last_success_at: new Date('2024-01-15T19:05:00Z'),
          run_count: 100,
          success_count: 95,
          error_count: 5,
          last_error: 'Connection timeout',
          success_rate: 95.00
        },
        {
          id: 3,
          name: '데이터 정리',
          job_type: 'cleanup',
          status: 'paused',
          interval: 'weekly',
          specific_times: ['02:00'],
          market_codes: null,
          next_run_at: new Date('2024-01-22T02:00:00Z'),
          last_run_at: new Date('2024-01-15T02:00:00Z'),
          last_success_at: new Date('2024-01-15T02:30:00Z'),
          run_count: 10,
          success_count: 10,
          error_count: 0,
          last_error: null,
          success_rate: 100.00
        }
      ]
      
      mockPool.query.mockResolvedValueOnce({ rows: mockJobs })
      
      const request = new NextRequest('http://localhost:3000/api/scheduler/jobs')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.data).toHaveLength(3)
      expect(data.data[0].name).toBe('상품 수집')
      expect(data.data[0].success_rate).toBe(96.00)
      expect(data.data[1].job_type).toBe('stock_sync')
      expect(data.data[2].status).toBe('paused')
      
      // Verify query structure
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('FROM schedule_jobs j WHERE j.is_active = true')
      )
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('ORDER BY j.priority DESC, j.name ASC')
      )
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('success_count::FLOAT / j.run_count * 100')
      )
    })
    
    it('성공률 계산을 올바르게 처리한다', async () => {
      const mockJobsWithStats = [
        {
          id: 1,
          name: '신규 작업',
          job_type: 'test',
          status: 'active',
          interval: 'daily',
          specific_times: null,
          market_codes: null,
          next_run_at: new Date('2024-01-16T00:00:00Z'),
          last_run_at: null,
          last_success_at: null,
          run_count: 0,
          success_count: 0,
          error_count: 0,
          last_error: null,
          success_rate: 0 // 실행된 적 없는 작업
        },
        {
          id: 2,
          name: '완벽한 작업',
          job_type: 'perfect',
          status: 'active',
          interval: 'hourly',
          specific_times: null,
          market_codes: null,
          next_run_at: new Date('2024-01-16T01:00:00Z'),
          last_run_at: new Date('2024-01-15T23:00:00Z'),
          last_success_at: new Date('2024-01-15T23:05:00Z'),
          run_count: 20,
          success_count: 20,
          error_count: 0,
          last_error: null,
          success_rate: 100.00
        }
      ]
      
      mockPool.query.mockResolvedValueOnce({ rows: mockJobsWithStats })
      
      const request = new NextRequest('http://localhost:3000/api/scheduler/jobs')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.data[0].success_rate).toBe(0) // 신규 작업
      expect(data.data[1].success_rate).toBe(100.00) // 완벽한 작업
    })
    
    it('다양한 작업 타입을 처리한다', async () => {
      const mockDiverseJobs = [
        {
          id: 1,
          name: '주문 동기화',
          job_type: 'order_sync',
          status: 'active',
          interval: 'every_30_minutes',
          specific_times: null,
          market_codes: ['coupang', 'smartstore'],
          next_run_at: new Date('2024-01-15T20:30:00Z'),
          last_run_at: new Date('2024-01-15T20:00:00Z'),
          last_success_at: new Date('2024-01-15T20:02:00Z'),
          run_count: 200,
          success_count: 195,
          error_count: 5,
          last_error: null,
          success_rate: 97.50
        },
        {
          id: 2,
          name: '알림 발송',
          job_type: 'notification',
          status: 'active',
          interval: 'manual',
          specific_times: null,
          market_codes: null,
          next_run_at: null,
          last_run_at: new Date('2024-01-15T19:30:00Z'),
          last_success_at: new Date('2024-01-15T19:31:00Z'),
          run_count: 5,
          success_count: 5,
          error_count: 0,
          last_error: null,
          success_rate: 100.00
        }
      ]
      
      mockPool.query.mockResolvedValueOnce({ rows: mockDiverseJobs })
      
      const request = new NextRequest('http://localhost:3000/api/scheduler/jobs')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.data[0].job_type).toBe('order_sync')
      expect(data.data[0].market_codes).toEqual(['coupang', 'smartstore'])
      expect(data.data[1].job_type).toBe('notification')
      expect(data.data[1].interval).toBe('manual')
    })
    
    it('빈 결과를 올바르게 처리한다', async () => {
      mockPool.query.mockResolvedValueOnce({ rows: [] })
      
      const request = new NextRequest('http://localhost:3000/api/scheduler/jobs')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.data).toHaveLength(0)
      expect(Array.isArray(data.data)).toBe(true)
    })
    
    it('데이터베이스 오류를 처리한다', async () => {
      mockPool.query.mockRejectedValueOnce(new Error('Database connection failed'))
      
      const request = new NextRequest('http://localhost:3000/api/scheduler/jobs')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.success).toBe(false)
      expect(data.error).toBe('스케줄 작업 조회 중 오류가 발생했습니다.')
    })
  })
  
  describe('POST', () => {
    const createRequest = (body: any) => {
      return new NextRequest('http://localhost:3000/api/scheduler/jobs', {
        method: 'POST',
        body: JSON.stringify(body)
      })
    }
    
    it('새 스케줄 작업을 성공적으로 생성한다', async () => {
      const jobData = {
        name: '새 상품 수집',
        job_type: 'collection',
        status: 'active',
        interval: 'daily',
        cron_expression: '0 9 * * *',
        specific_times: ['09:00'],
        market_codes: ['ownerclan'],
        account_ids: [1, 2],
        parameters: {
          batch_size: 1000,
          retry_count: 3
        },
        max_retries: 5,
        timeout_minutes: 60,
        priority: 8
      }
      
      mockPool.query.mockResolvedValueOnce({ rows: [{ id: 100 }] })
      
      const request = createRequest(jobData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.data.id).toBe(100)
      
      // Verify insert query with all parameters
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO schedule_jobs'),
        [
          '새 상품 수집',
          'collection',
          'active',
          'daily',
          '0 9 * * *',
          ['09:00'],
          ['ownerclan'],
          [1, 2],
          { batch_size: 1000, retry_count: 3 },
          5,
          60,
          8
        ]
      )
    })
    
    it('기본값으로 스케줄 작업을 생성한다', async () => {
      const minimalJobData = {
        name: '최소 작업',
        job_type: 'simple_task',
        interval: 'hourly'
      }
      
      mockPool.query.mockResolvedValueOnce({ rows: [{ id: 200 }] })
      
      const request = createRequest(minimalJobData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.data.id).toBe(200)
      
      // Verify default values are applied
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.any(String),
        [
          '최소 작업',
          'simple_task',
          'active', // default status
          'hourly',
          undefined, // cron_expression
          undefined, // specific_times
          undefined, // market_codes
          undefined, // account_ids
          {}, // default parameters
          3, // default max_retries
          30, // default timeout_minutes
          5 // default priority
        ]
      )
    })
    
    it('복잡한 파라미터를 처리한다', async () => {
      const complexJobData = {
        name: '복잡한 작업',
        job_type: 'advanced_collection',
        status: 'paused',
        interval: 'custom',
        cron_expression: '0 */2 * * 1-5',
        specific_times: ['09:00', '14:00', '18:00'],
        market_codes: ['ownerclan', 'zentrade', 'coupang'],
        account_ids: [1, 3, 5, 7],
        parameters: {
          collection_type: 'incremental',
          filters: {
            category: 'electronics',
            price_range: { min: 10000, max: 500000 }
          },
          notifications: {
            on_success: true,
            on_error: true,
            email: 'admin@company.com'
          }
        },
        max_retries: 10,
        timeout_minutes: 120,
        priority: 10
      }
      
      mockPool.query.mockResolvedValueOnce({ rows: [{ id: 300 }] })
      
      const request = createRequest(complexJobData)
      const response = await POST(request)
      
      expect(response.status).toBe(200)
      
      // Verify complex parameters are passed correctly
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.any(String),
        expect.arrayContaining([
          '복잡한 작업',
          'advanced_collection',
          'paused',
          'custom',
          '0 */2 * * 1-5',
          ['09:00', '14:00', '18:00'],
          ['ownerclan', 'zentrade', 'coupang'],
          [1, 3, 5, 7],
          complexJobData.parameters,
          10,
          120,
          10
        ])
      )
    })
    
    it('null 값들을 올바르게 처리한다', async () => {
      const jobWithNulls = {
        name: 'Null 테스트',
        job_type: 'test',
        status: 'active',
        interval: 'daily',
        cron_expression: null,
        specific_times: null,
        market_codes: null,
        account_ids: null,
        parameters: null
      }
      
      mockPool.query.mockResolvedValueOnce({ rows: [{ id: 400 }] })
      
      const request = createRequest(jobWithNulls)
      const response = await POST(request)
      
      expect(response.status).toBe(200)
      
      // Verify null handling
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.any(String),
        [
          'Null 테스트',
          'test',
          'active',
          'daily',
          null,
          null,
          null,
          null,
          {}, // null parameters become empty object
          3,
          30,
          5
        ]
      )
    })
    
    it('배열과 객체 타입을 올바르게 처리한다', async () => {
      const jobWithArraysAndObjects = {
        name: '배열 객체 테스트',
        job_type: 'complex',
        interval: 'weekly',
        specific_times: ['06:00', '12:00', '18:00'],
        market_codes: ['market1', 'market2'],
        account_ids: [10, 20, 30],
        parameters: {
          nested: {
            array: [1, 2, 3],
            object: { key: 'value' }
          }
        }
      }
      
      mockPool.query.mockResolvedValueOnce({ rows: [{ id: 500 }] })
      
      const request = createRequest(jobWithArraysAndObjects)
      const response = await POST(request)
      
      expect(response.status).toBe(200)
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.any(String),
        expect.arrayContaining([
          ['06:00', '12:00', '18:00'],
          ['market1', 'market2'],
          [10, 20, 30],
          jobWithArraysAndObjects.parameters
        ])
      )
    })
    
    it('데이터베이스 오류를 처리한다', async () => {
      const jobData = {
        name: '오류 테스트',
        job_type: 'error_test',
        interval: 'daily'
      }
      
      mockPool.query.mockRejectedValueOnce(new Error('Insert failed'))
      
      const request = createRequest(jobData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.success).toBe(false)
      expect(data.error).toBe('스케줄 작업 생성 중 오류가 발생했습니다.')
    })
    
    it('잘못된 JSON 형식을 처리한다', async () => {
      const request = new NextRequest('http://localhost:3000/api/scheduler/jobs', {
        method: 'POST',
        body: 'invalid json'
      })
      
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.success).toBe(false)
      expect(data.error).toBe('스케줄 작업 생성 중 오류가 발생했습니다.')
    })
    
    it('상태별 작업 생성을 처리한다', async () => {
      const statusTests = [
        { status: 'active', expected: 'active' },
        { status: 'paused', expected: 'paused' },
        { status: 'disabled', expected: 'disabled' },
        { status: undefined, expected: 'active' } // default
      ]
      
      for (const [index, test] of statusTests.entries()) {
        mockPool.query.mockResolvedValueOnce({ rows: [{ id: 600 + index }] })
        
        const jobData = {
          name: `상태 테스트 ${test.status || 'default'}`,
          job_type: 'status_test',
          interval: 'daily',
          status: test.status
        }
        
        const request = createRequest(jobData)
        const response = await POST(request)
        
        expect(response.status).toBe(200)
        expect(mockPool.query).toHaveBeenLastCalledWith(
          expect.any(String),
          expect.arrayContaining([test.expected])
        )
      }
    })
  })
})