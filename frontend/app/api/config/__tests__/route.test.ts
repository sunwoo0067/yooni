import { GET, POST, DELETE } from '../route'
import { NextRequest } from 'next/server'

// Mock the pg pool
const mockPool = {
  query: jest.fn()
}

jest.mock('pg', () => ({
  Pool: jest.fn().mockImplementation(() => mockPool)
}))

describe('/api/config', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  describe('GET', () => {
    it('모든 설정을 카테고리별로 그룹화하여 반환한다', async () => {
      const mockConfigs = [
        {
          id: 1,
          category: 'database',
          key: 'max_connections',
          value: '100',
          description: '최대 연결 수',
          data_type: 'integer',
          is_active: true,
          created_at: new Date('2024-01-01'),
          updated_at: new Date('2024-01-01'),
          encrypted: false
        },
        {
          id: 2,
          category: 'database',
          key: 'timeout',
          value: '30000',
          description: '연결 타임아웃',
          data_type: 'integer',
          is_active: true,
          created_at: new Date('2024-01-01'),
          updated_at: new Date('2024-01-01'),
          encrypted: false
        },
        {
          id: 3,
          category: 'api',
          key: 'rate_limit',
          value: '1000',
          description: 'API 요청 제한',
          data_type: 'integer',
          is_active: true,
          created_at: new Date('2024-01-01'),
          updated_at: new Date('2024-01-01'),
          encrypted: false
        }
      ]
      
      mockPool.query.mockResolvedValueOnce({ rows: mockConfigs })
      
      const request = new NextRequest('http://localhost:3000/api/config')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.total).toBe(3)
      expect(data.data.database).toHaveLength(2)
      expect(data.data.api).toHaveLength(1)
      expect(data.data.database[0].key).toBe('max_connections')
      expect(data.data.api[0].key).toBe('rate_limit')
      
      // Verify query
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('FROM system_configs sc WHERE sc.is_active = true'),
        []
      )
    })
    
    it('카테고리 필터를 적용한다', async () => {
      const mockConfigs = [
        {
          id: 1,
          category: 'database',
          key: 'max_connections',
          value: '100',
          description: '최대 연결 수',
          data_type: 'integer',
          is_active: true,
          created_at: new Date('2024-01-01'),
          updated_at: new Date('2024-01-01'),
          encrypted: false
        }
      ]
      
      mockPool.query.mockResolvedValueOnce({ rows: mockConfigs })
      
      const request = new NextRequest('http://localhost:3000/api/config?category=database')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.data.database).toHaveLength(1)
      
      // Verify category filter
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('AND sc.category = $1'),
        ['database']
      )
    })
    
    it('키 필터를 적용한다', async () => {
      const mockConfigs = [
        {
          id: 1,
          category: 'database',
          key: 'max_connections',
          value: '100',
          description: '최대 연결 수',
          data_type: 'integer',
          is_active: true,
          created_at: new Date('2024-01-01'),
          updated_at: new Date('2024-01-01'),
          encrypted: false
        }
      ]
      
      mockPool.query.mockResolvedValueOnce({ rows: mockConfigs })
      
      const request = new NextRequest('http://localhost:3000/api/config?key=max_connections')
      const response = await GET(request)
      
      expect(response.status).toBe(200)
      
      // Verify key filter
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('AND sc.key = $1'),
        ['max_connections']
      )
    })
    
    it('카테고리와 키 필터를 모두 적용한다', async () => {
      mockPool.query.mockResolvedValueOnce({ rows: [] })
      
      const request = new NextRequest('http://localhost:3000/api/config?category=database&key=max_connections')
      const response = await GET(request)
      
      expect(response.status).toBe(200)
      
      // Verify both filters
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('AND sc.category = $1 AND sc.key = $2'),
        ['database', 'max_connections']
      )
    })
    
    it('민감한 설정 값을 마스킹한다', async () => {
      const mockSensitiveConfigs = [
        {
          id: 1,
          category: 'auth',
          key: 'JWT_SECRET',
          value: 'super-secret-key',
          description: 'JWT 비밀키',
          data_type: 'string',
          is_active: true,
          created_at: new Date('2024-01-01'),
          updated_at: new Date('2024-01-01'),
          encrypted: false
        },
        {
          id: 2,
          category: 'database',
          key: 'DB_PASSWORD',
          value: 'password123',
          description: '데이터베이스 비밀번호',
          data_type: 'string',
          is_active: true,
          created_at: new Date('2024-01-01'),
          updated_at: new Date('2024-01-01'),
          encrypted: false
        },
        {
          id: 3,
          category: 'encryption',
          key: 'api_key',
          value: 'encrypted-value',
          description: '암호화된 API 키',
          data_type: 'string',
          is_active: true,
          created_at: new Date('2024-01-01'),
          updated_at: new Date('2024-01-01'),
          encrypted: true
        }
      ]
      
      mockPool.query.mockResolvedValueOnce({ rows: mockSensitiveConfigs })
      
      const request = new NextRequest('http://localhost:3000/api/config')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.data.auth[0].value).toBe('********')
      expect(data.data.auth[0].masked).toBe(true)
      expect(data.data.database[0].value).toBe('********')
      expect(data.data.database[0].masked).toBe(true)
      expect(data.data.encryption[0].value).toBe('********')
      expect(data.data.encryption[0].masked).toBe(true)
    })
    
    it('빈 결과를 올바르게 처리한다', async () => {
      mockPool.query.mockResolvedValueOnce({ rows: [] })
      
      const request = new NextRequest('http://localhost:3000/api/config?category=nonexistent')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.data).toEqual({})
      expect(data.total).toBe(0)
    })
    
    it('데이터베이스 오류를 처리한다', async () => {
      mockPool.query.mockRejectedValueOnce(new Error('Database connection failed'))
      
      const request = new NextRequest('http://localhost:3000/api/config')
      const response = await GET(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.success).toBe(false)
      expect(data.error).toBe('설정 조회 중 오류가 발생했습니다.')
    })
  })
  
  describe('POST', () => {
    const createRequest = (body: any) => {
      return new NextRequest('http://localhost:3000/api/config', {
        method: 'POST',
        body: JSON.stringify(body)
      })
    }
    
    it('새 설정을 성공적으로 저장한다', async () => {
      const configData = {
        category: 'api',
        key: 'timeout',
        value: '5000',
        description: 'API 타임아웃',
        data_type: 'integer',
        user: 'admin'
      }
      
      const mockResult = {
        id: 10,
        ...configData,
        value: '5000',
        created_at: new Date(),
        updated_at: new Date()
      }
      
      mockPool.query.mockResolvedValueOnce({ rows: [mockResult] })
      
      const request = createRequest(configData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.data.key).toBe('timeout')
      
      // Verify insert query
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('INSERT INTO system_configs'),
        ['api', 'timeout', '5000', 'API 타임아웃', 'integer', 'admin', 'admin']
      )
    })
    
    it('필수 필드가 없을 때 오류를 반환한다', async () => {
      const invalidData = {
        value: 'some value'
        // category and key missing
      }
      
      const request = createRequest(invalidData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(400)
      expect(data.success).toBe(false)
      expect(data.error).toBe('카테고리와 키는 필수입니다.')
    })
    
    it('정수 타입 검증을 수행한다', async () => {
      const invalidIntegerData = {
        category: 'test',
        key: 'invalid_number',
        value: 'not-a-number',
        data_type: 'integer'
      }
      
      const request = createRequest(invalidIntegerData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(400)
      expect(data.success).toBe(false)
      expect(data.error).toBe('정수 값이 유효하지 않습니다.')
    })
    
    it('정수 값을 올바르게 변환한다', async () => {
      const integerData = {
        category: 'test',
        key: 'number_value',
        value: '123',
        data_type: 'integer'
      }
      
      mockPool.query.mockResolvedValueOnce({ rows: [{ id: 1, ...integerData }] })
      
      const request = createRequest(integerData)
      const response = await POST(request)
      
      expect(response.status).toBe(200)
      
      // Verify integer conversion
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.any(String),
        expect.arrayContaining(['123']) // String value in query
      )
    })
    
    it('불린 타입을 올바르게 변환한다', async () => {
      const booleanData = {
        category: 'test',
        key: 'enabled',
        value: 'true',
        data_type: 'boolean'
      }
      
      mockPool.query.mockResolvedValueOnce({ rows: [{ id: 1, ...booleanData }] })
      
      const request = createRequest(booleanData)
      const response = await POST(request)
      
      expect(response.status).toBe(200)
      
      // Verify boolean conversion
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.any(String),
        expect.arrayContaining(['true']) // Converted to string
      )
    })
    
    it('JSON 타입 검증을 수행한다', async () => {
      const invalidJsonData = {
        category: 'test',
        key: 'config_json',
        value: '{invalid json}',
        data_type: 'json'
      }
      
      const request = createRequest(invalidJsonData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(400)
      expect(data.success).toBe(false)
      expect(data.error).toBe('JSON 값이 유효하지 않습니다.')
    })
    
    it('유효한 JSON을 처리한다', async () => {
      const validJsonData = {
        category: 'test',
        key: 'config_json',
        value: '{"key": "value"}',
        data_type: 'json'
      }
      
      mockPool.query.mockResolvedValueOnce({ rows: [{ id: 1, ...validJsonData }] })
      
      const request = createRequest(validJsonData)
      const response = await POST(request)
      
      expect(response.status).toBe(200)
    })
    
    it('기본 데이터 타입을 string으로 설정한다', async () => {
      const defaultData = {
        category: 'test',
        key: 'simple_value',
        value: 'test value'
        // data_type not specified
      }
      
      mockPool.query.mockResolvedValueOnce({ rows: [{ id: 1, ...defaultData }] })
      
      const request = createRequest(defaultData)
      const response = await POST(request)
      
      expect(response.status).toBe(200)
      
      // Verify default data_type
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.any(String),
        expect.arrayContaining(['string'])
      )
    })
    
    it('데이터베이스 오류를 처리한다', async () => {
      const configData = {
        category: 'test',
        key: 'error_test',
        value: 'value'
      }
      
      mockPool.query.mockRejectedValueOnce(new Error('Database error'))
      
      const request = createRequest(configData)
      const response = await POST(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.success).toBe(false)
      expect(data.error).toBe('설정 저장 중 오류가 발생했습니다.')
    })
  })
  
  describe('DELETE', () => {
    it('설정을 성공적으로 비활성화한다', async () => {
      const mockResult = {
        id: 1,
        category: 'test',
        key: 'to_delete',
        is_active: false,
        updated_at: new Date()
      }
      
      mockPool.query.mockResolvedValueOnce({ rows: [mockResult] })
      
      const request = new NextRequest('http://localhost:3000/api/config?category=test&key=to_delete', {
        method: 'DELETE'
      })
      const response = await DELETE(request)
      const data = await response.json()
      
      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.data.is_active).toBe(false)
      
      // Verify update query
      expect(mockPool.query).toHaveBeenCalledWith(
        expect.stringContaining('UPDATE system_configs SET is_active = false'),
        ['test', 'to_delete']
      )
    })
    
    it('카테고리가 없을 때 오류를 반환한다', async () => {
      const request = new NextRequest('http://localhost:3000/api/config?key=test_key', {
        method: 'DELETE'
      })
      const response = await DELETE(request)
      const data = await response.json()
      
      expect(response.status).toBe(400)
      expect(data.success).toBe(false)
      expect(data.error).toBe('카테고리와 키는 필수입니다.')
    })
    
    it('키가 없을 때 오류를 반환한다', async () => {
      const request = new NextRequest('http://localhost:3000/api/config?category=test', {
        method: 'DELETE'
      })
      const response = await DELETE(request)
      const data = await response.json()
      
      expect(response.status).toBe(400)
      expect(data.success).toBe(false)
      expect(data.error).toBe('카테고리와 키는 필수입니다.')
    })
    
    it('존재하지 않는 설정에 대해 404를 반환한다', async () => {
      mockPool.query.mockResolvedValueOnce({ rows: [] })
      
      const request = new NextRequest('http://localhost:3000/api/config?category=nonexistent&key=nonexistent', {
        method: 'DELETE'
      })
      const response = await DELETE(request)
      const data = await response.json()
      
      expect(response.status).toBe(404)
      expect(data.success).toBe(false)
      expect(data.error).toBe('설정을 찾을 수 없습니다.')
    })
    
    it('데이터베이스 오류를 처리한다', async () => {
      mockPool.query.mockRejectedValueOnce(new Error('Database error'))
      
      const request = new NextRequest('http://localhost:3000/api/config?category=test&key=test_key', {
        method: 'DELETE'
      })
      const response = await DELETE(request)
      const data = await response.json()
      
      expect(response.status).toBe(500)
      expect(data.success).toBe(false)
      expect(data.error).toBe('설정 삭제 중 오류가 발생했습니다.')
    })
  })
})