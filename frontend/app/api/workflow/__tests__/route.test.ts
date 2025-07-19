import { GET, POST, PUT } from '../route'
import { NextRequest } from 'next/server'

// Mock the pg pool
const mockPool = {
  query: jest.fn(),
  connect: jest.fn()
}

const mockClient = {
  query: jest.fn(),
  release: jest.fn()
}

jest.mock('pg', () => ({
  Pool: jest.fn().mockImplementation(() => mockPool)
}))

describe('/api/workflow', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockPool.connect.mockResolvedValue(mockClient)
  })
  
  describe('GET', () => {
    it('워크플로우 목록을 성공적으로 반환한다', async () => {
      const mockWorkflows = [
        {
          id: 1,
          name: '상품 가격 모니터링',
          description: '상품 가격 변동 시 알림',
          trigger_type: 'event',
          config: { event_type: 'price_change' },
          is_active: true,
          created_at: new Date('2024-01-01'),
          execution_count: '5',
          last_executed_at: new Date('2024-01-15'),
          avg_execution_time: '150.5'
        },
        {
          id: 2,
          name: '재고 부족 알림',
          description: '재고가 부족할 때 자동 알림',
          trigger_type: 'schedule',
          config: { cron: '0 9 * * *' },
          is_active: true,
          created_at: new Date('2024-01-02'),
          execution_count: '10',
          last_executed_at: new Date('2024-01-14'),
          avg_execution_time: '89.2'
        }
      ]
      
      mockPool.query.mockResolvedValueOnce({
        rows: mockWorkflows,
        rowCount: 2
      })
      
      const request = new NextRequest('http://localhost:3000/api/workflow')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.workflows).toHaveLength(2)
      expect(data.total).toBe(2)
      expect(data.workflows[0].name).toBe('상품 가격 모니터링')
      expect(data.workflows[1].trigger_type).toBe('schedule')
      
      // Verify complex JOIN query
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('LEFT JOIN workflow_executions we ON wd.id = we.workflow_id'),
        []
      )
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('GROUP BY wd.id'),
        []
      )
    })
    
    it('트리거 타입 필터를 적용한다', async () => {
      mockPool.query.mockResolvedValueOnce({
        rows: [
          {
            id: 1,
            trigger_type: 'event',
            execution_count: '3'
          }
        ],
        rowCount: 1
      })
      
      const request = new NextRequest('http://localhost:3000/api/workflow?trigger_type=event')
      const response = await GET(request)
      
      expect(response.status).toBe(200)
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('AND wd.trigger_type = $1'),
        ['event']
      )
    })
    
    it('활성 상태 필터를 적용한다', async () => {
      mockPool.query.mockResolvedValueOnce({
        rows: [],
        rowCount: 0
      })
      
      const request = new NextRequest('http://localhost:3000/api/workflow?is_active=true')
      const response = await GET(request)
      
      expect(response.status).toBe(200)
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('AND wd.is_active = $1'),
        [true]
      )
    })
    
    it('복합 필터를 적용한다', async () => {
      mockPool.query.mockResolvedValueOnce({
        rows: [],
        rowCount: 0
      })
      
      const request = new NextRequest('http://localhost:3000/api/workflow?trigger_type=schedule&is_active=false')
      const response = await GET(request)
      
      expect(response.status).toBe(200)
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('AND wd.trigger_type = $1 AND wd.is_active = $2'),
        ['schedule', false]
      )
    })
    
    it('빈 결과를 올바르게 처리한다', async () => {
      mockPool.query.mockResolvedValueOnce({
        rows: [],
        rowCount: 0
      })
      
      const request = new NextRequest('http://localhost:3000/api/workflow')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.workflows).toHaveLength(0)
      expect(data.total).toBe(0)
    })
    
    it('데이터베이스 오류를 처리한다', async () => {
      mockPool.query.mockRejectedValueOnce(new Error('Database connection failed'))
      
      const request = new NextRequest('http://localhost:3000/api/workflow')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to fetch workflows')
    })
    
    it('실행 통계를 올바르게 집계한다', async () => {
      const mockWorkflowWithStats = [
        {
          id: 1,
          name: '통계 테스트',
          execution_count: '25',
          last_executed_at: new Date('2024-01-15T10:30:00Z'),
          avg_execution_time: '1250.75'
        }
      ]
      
      mockPool.query.mockResolvedValueOnce({
        rows: mockWorkflowWithStats,
        rowCount: 1
      })
      
      const request = new NextRequest('http://localhost:3000/api/workflow')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.workflows[0].execution_count).toBe('25')
      expect(data.workflows[0].avg_execution_time).toBe('1250.75')
      
      // Verify aggregation functions in query
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('COUNT(we.id) as execution_count'),
        []
      )
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('MAX(we.started_at) as last_executed_at'),
        []
      )
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('AVG(we.execution_time_ms) as avg_execution_time'),
        []
      )
    })
  })
  
  describe('POST', () => {
    const createRequest = (body: any) => {
      return new NextRequest('http://localhost:3000/api/workflow', {
        method: 'POST',
        body: JSON.stringify(body)
      })
    }
    
    it('새 워크플로우를 성공적으로 생성한다', async () => {
      const workflowData = {
        name: '새 워크플로우',
        description: '테스트용 워크플로우',
        trigger_type: 'schedule',
        config: { cron: '0 8 * * *' },
        rules: [
          {
            condition_type: 'stock_level',
            condition_config: { threshold: 10 },
            action_type: 'send_email',
            action_config: { to: 'admin@company.com' }
          }
        ]
      }
      
      // Mock workflow insertion
      mockClient.query
        .mockResolvedValueOnce(undefined) // BEGIN
        .mockResolvedValueOnce({ rows: [{ id: 100 }] }) // INSERT workflow
        .mockResolvedValueOnce(undefined) // INSERT rule
        .mockResolvedValueOnce(undefined) // COMMIT
      
      const request = createRequest(workflowData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.workflow_id).toBe(100)
      expect(data.message).toBe('워크플로우가 생성되었습니다')
      
      // Verify transaction
      expect(mockClient.query).toHaveBeenCalledWith('BEGIN')
      expect(mockClient.query).toHaveBeenCalledWith('COMMIT')
      expect(mockClient.release).toHaveBeenCalled()
      
      // Verify workflow creation
      expect(mockClient.query).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO workflow_definitions'),
        ['새 워크플로우', '테스트용 워크플로우', 'schedule', { cron: '0 8 * * *' }]
      )
      
      // Verify rule creation
      expect(mockClient.query).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO workflow_rules'),
        [100, 1, 'stock_level', { threshold: 10 }, 'send_email', { to: 'admin@company.com' }]
      )
    })
    
    it('이벤트 트리거가 있는 워크플로우를 생성한다', async () => {
      const eventWorkflowData = {
        name: '이벤트 워크플로우',
        description: '이벤트 기반 워크플로우',
        trigger_type: 'event',
        config: {
          event_type: 'product_updated',
          event_source: 'product_service',
          filter: { category: 'electronics' }
        },
        rules: []
      }
      
      mockClient.query
        .mockResolvedValueOnce(undefined) // BEGIN
        .mockResolvedValueOnce({ rows: [{ id: 200 }] }) // INSERT workflow
        .mockResolvedValueOnce(undefined) // INSERT event trigger
        .mockResolvedValueOnce(undefined) // COMMIT
      
      const request = createRequest(eventWorkflowData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.workflow_id).toBe(200)
      
      // Verify event trigger creation
      expect(mockClient.query).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO event_triggers'),
        [
          'product_updated',
          'product_service', 
          200,
          { category: 'electronics' }
        ]
      )
    })
    
    it('여러 규칙을 순서대로 생성한다', async () => {
      const multiRuleWorkflow = {
        name: '다중 규칙 워크플로우',
        description: '여러 규칙을 가진 워크플로우',
        trigger_type: 'manual',
        config: {},
        rules: [
          {
            condition_type: 'price_change',
            condition_config: { percentage: 10 },
            action_type: 'update_inventory',
            action_config: { adjust: true }
          },
          {
            condition_type: 'stock_low',
            condition_config: { threshold: 5 },
            action_type: 'notify_supplier',
            action_config: { urgent: true }
          },
          {
            condition_type: 'always',
            condition_config: {},
            action_type: 'log_activity',
            action_config: { level: 'info' }
          }
        ]
      }
      
      mockClient.query
        .mockResolvedValueOnce(undefined) // BEGIN
        .mockResolvedValueOnce({ rows: [{ id: 300 }] }) // INSERT workflow
        .mockResolvedValueOnce(undefined) // INSERT rule 1
        .mockResolvedValueOnce(undefined) // INSERT rule 2
        .mockResolvedValueOnce(undefined) // INSERT rule 3
        .mockResolvedValueOnce(undefined) // COMMIT
      
      const request = createRequest(multiRuleWorkflow)
      const response = await POST(request)
      
      expect(response.status).toBe(200)
      
      // Verify rules were created with correct order
      expect(mockClient.query).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO workflow_rules'),
        [300, 1, 'price_change', { percentage: 10 }, 'update_inventory', { adjust: true }]
      )
      expect(mockClient.query).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO workflow_rules'),
        [300, 2, 'stock_low', { threshold: 5 }, 'notify_supplier', { urgent: true }]
      )
      expect(mockClient.query).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO workflow_rules'),
        [300, 3, 'always', {}, 'log_activity', { level: 'info' }]
      )
    })
    
    it('규칙이 없는 워크플로우를 생성한다', async () => {
      const noRulesWorkflow = {
        name: '규칙 없는 워크플로우',
        description: '규칙이 없는 단순 워크플로우',
        trigger_type: 'manual',
        config: {},
        rules: []
      }
      
      mockClient.query
        .mockResolvedValueOnce(undefined) // BEGIN
        .mockResolvedValueOnce({ rows: [{ id: 400 }] }) // INSERT workflow
        .mockResolvedValueOnce(undefined) // COMMIT
      
      const request = createRequest(noRulesWorkflow)
      const response = await POST(request)
      
      expect(response.status).toBe(200)
      
      // Verify no rules were inserted
      const ruleCalls = mockClient.query.mock.calls.filter(call => 
        call[0].includes('INSERT INTO workflow_rules')
      )
      expect(ruleCalls).toHaveLength(0)
    })
    
    it('트랜잭션 오류 시 롤백한다', async () => {
      const workflowData = {
        name: '오류 테스트',
        trigger_type: 'schedule',
        config: {},
        rules: []
      }
      
      mockClient.query
        .mockResolvedValueOnce(undefined) // BEGIN
        .mockResolvedValueOnce({ rows: [{ id: 500 }] }) // INSERT workflow
        .mockRejectedValueOnce(new Error('Rule insertion failed')) // Error
      
      const request = createRequest(workflowData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to create workflow')
      
      // Verify rollback was called
      expect(mockClient.query).toHaveBeenCalledWith('ROLLBACK')
      expect(mockClient.release).toHaveBeenCalled()
    })
    
    it('잘못된 JSON 형식을 처리한다', async () => {
      const request = new NextRequest('http://localhost:3000/api/workflow', {
        method: 'POST',
        body: 'invalid json'
      })
      
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to create workflow')
    })
    
    it('이벤트 트리거 없이 이벤트 타입 워크플로우를 생성한다', async () => {
      const incompleteEventWorkflow = {
        name: '불완전한 이벤트 워크플로우',
        trigger_type: 'event',
        config: { event_type: 'test' }, // event_source missing
        rules: []
      }
      
      mockClient.query
        .mockResolvedValueOnce(undefined) // BEGIN
        .mockResolvedValueOnce({ rows: [{ id: 600 }] }) // INSERT workflow
        .mockResolvedValueOnce(undefined) // COMMIT (no event trigger)
      
      const request = createRequest(incompleteEventWorkflow)
      const response = await POST(request)
      
      expect(response.status).toBe(200)
      
      // Verify no event trigger was created
      const eventTriggerCalls = mockClient.query.mock.calls.filter(call =>
        call[0].includes('INSERT INTO event_triggers')
      )
      expect(eventTriggerCalls).toHaveLength(0)
    })
  })
  
  describe('PUT', () => {
    const createRequest = (body: any) => {
      return new NextRequest('http://localhost:3000/api/workflow', {
        method: 'PUT',
        body: JSON.stringify(body)
      })
    }
    
    it('워크플로우를 활성화한다', async () => {
      mockPool.query.mockResolvedValueOnce({ rowCount: 1 })
      
      const request = createRequest({
        id: 1,
        is_active: true
      })
      const response = await PUT(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.message).toBe('워크플로우가 활성화되었습니다')
      
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('UPDATE workflow_definitions SET is_active = $1'),
        [true, 1]
      )
    })
    
    it('워크플로우를 비활성화한다', async () => {
      mockPool.query.mockResolvedValueOnce({ rowCount: 1 })
      
      const request = createRequest({
        id: 2,
        is_active: false
      })
      const response = await PUT(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.message).toBe('워크플로우가 비활성화되었습니다')
      
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('UPDATE workflow_definitions SET is_active = $1'),
        [false, 2]
      )
    })
    
    it('is_active가 없는 요청을 거부한다', async () => {
      const request = createRequest({
        id: 1,
        name: 'New Name' // is_active not provided
      })
      const response = await PUT(request)
      const data = await response.json()
      
      expect(response.status).toBe(400)
      expect(data.error).toBe('Invalid update request')
    })
    
    it('데이터베이스 업데이트 오류를 처리한다', async () => {
      mockPool.query.mockRejectedValueOnce(new Error('Update failed'))
      
      const request = createRequest({
        id: 1,
        is_active: true
      })
      const response = await PUT(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to update workflow')
    })
    
    it('잘못된 JSON을 처리한다', async () => {
      const request = new NextRequest('http://localhost:3000/api/workflow', {
        method: 'PUT',
        body: 'invalid json'
      })
      
      const response = await PUT(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to update workflow')
    })
  })
})