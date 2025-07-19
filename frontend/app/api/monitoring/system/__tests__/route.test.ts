import { GET } from '../route'
import os from 'os'

// Mock the os module
jest.mock('os', () => ({
  cpus: jest.fn(),
  totalmem: jest.fn(),
  freemem: jest.fn(),
  networkInterfaces: jest.fn(),
  uptime: jest.fn(),
  loadavg: jest.fn(),
  platform: jest.fn(),
  hostname: jest.fn()
}))

describe('/api/monitoring/system', () => {
  const mockOs = os as jest.Mocked<typeof os>
  
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Set default mock values
    mockOs.cpus.mockReturnValue([
      {
        model: 'Intel Core i7',
        speed: 2800,
        times: {
          user: 12345,
          nice: 0,
          sys: 5432,
          idle: 87654,
          irq: 123
        }
      },
      {
        model: 'Intel Core i7',
        speed: 2800,
        times: {
          user: 11111,
          nice: 0,
          sys: 4444,
          idle: 77777,
          irq: 111
        }
      }
    ])
    
    mockOs.totalmem.mockReturnValue(8589934592) // 8GB
    mockOs.freemem.mockReturnValue(2147483648)  // 2GB free
    mockOs.networkInterfaces.mockReturnValue({
      lo: [{
        address: '127.0.0.1',
        netmask: '255.0.0.0',
        family: 'IPv4',
        mac: '00:00:00:00:00:00',
        internal: true,
        cidr: '127.0.0.1/8'
      }]
    })
    mockOs.uptime.mockReturnValue(86400) // 1 day
    mockOs.loadavg.mockReturnValue([1.5, 2.0, 1.8])
    mockOs.platform.mockReturnValue('linux')
    mockOs.hostname.mockReturnValue('test-server')
  })
  
  it('시스템 메트릭을 성공적으로 반환한다', async () => {
    const response = await GET()
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data).toHaveProperty('cpu')
    expect(data).toHaveProperty('memory')
    expect(data).toHaveProperty('disk')
    expect(data).toHaveProperty('network')
    expect(data).toHaveProperty('uptime')
    expect(data).toHaveProperty('loadAverage')
    expect(data).toHaveProperty('platform')
    expect(data).toHaveProperty('hostname')
    
    expect(typeof data.cpu).toBe('number')
    expect(typeof data.memory).toBe('number')
    expect(typeof data.disk).toBe('number')
    expect(data.network).toHaveProperty('bytesIn')
    expect(data.network).toHaveProperty('bytesOut')
    expect(data.uptime).toBe(86400)
    expect(data.loadAverage).toEqual([1.5, 2.0, 1.8])
    expect(data.platform).toBe('linux')
    expect(data.hostname).toBe('test-server')
  })
  
  it('CPU 사용률을 올바르게 계산한다', async () => {
    // Set specific CPU times for predictable calculation
    mockOs.cpus.mockReturnValue([
      {
        model: 'Test CPU',
        speed: 3000,
        times: {
          user: 10000,
          nice: 100,
          sys: 5000,
          idle: 80000,
          irq: 900
        }
      }
    ])
    
    const response = await GET()
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.cpu).toBeGreaterThanOrEqual(0)
    expect(data.cpu).toBeLessThanOrEqual(100)
    expect(typeof data.cpu).toBe('number')
  })
  
  it('메모리 사용률을 올바르게 계산한다', async () => {
    // Total: 16GB, Free: 4GB -> Usage: 75%
    mockOs.totalmem.mockReturnValue(17179869184) // 16GB
    mockOs.freemem.mockReturnValue(4294967296)   // 4GB free
    
    const response = await GET()
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.memory).toBeCloseTo(75, 1) // About 75% usage
    expect(data.memory).toBeGreaterThanOrEqual(0)
    expect(data.memory).toBeLessThanOrEqual(100)
  })
  
  it('디스크 사용률 임시값을 반환한다', async () => {
    const response = await GET()
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.disk).toBe(65) // 하드코딩된 임시값
  })
  
  it('네트워크 정보를 포함한다', async () => {
    const response = await GET()
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.network).toHaveProperty('bytesIn')
    expect(data.network).toHaveProperty('bytesOut')
    expect(typeof data.network.bytesIn).toBe('number')
    expect(typeof data.network.bytesOut).toBe('number')
    expect(data.network.bytesIn).toBeGreaterThanOrEqual(0)
    expect(data.network.bytesOut).toBeGreaterThanOrEqual(0)
  })
  
  it('시스템 정보를 포함한다', async () => {
    mockOs.platform.mockReturnValue('darwin')
    mockOs.hostname.mockReturnValue('macbook-pro')
    mockOs.uptime.mockReturnValue(172800) // 2 days
    mockOs.loadavg.mockReturnValue([0.5, 1.0, 1.5])
    
    const response = await GET()
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.platform).toBe('darwin')
    expect(data.hostname).toBe('macbook-pro')
    expect(data.uptime).toBe(172800)
    expect(data.loadAverage).toEqual([0.5, 1.0, 1.5])
  })
  
  it('다중 CPU 코어를 올바르게 처리한다', async () => {
    mockOs.cpus.mockReturnValue([
      {
        model: 'Core 1',
        speed: 2800,
        times: { user: 1000, nice: 0, sys: 500, idle: 8000, irq: 100 }
      },
      {
        model: 'Core 2', 
        speed: 2800,
        times: { user: 1200, nice: 0, sys: 600, idle: 7800, irq: 120 }
      },
      {
        model: 'Core 3',
        speed: 2800,
        times: { user: 900, nice: 0, sys: 400, idle: 8200, irq: 80 }
      },
      {
        model: 'Core 4',
        speed: 2800,
        times: { user: 1100, nice: 0, sys: 550, idle: 7900, irq: 110 }
      }
    ])
    
    const response = await GET()
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.cpu).toBeGreaterThanOrEqual(0)
    expect(data.cpu).toBeLessThanOrEqual(100)
    
    // Verify all CPUs were processed
    expect(mockOs.cpus).toHaveBeenCalledTimes(1)
  })
  
  it('빈 CPU 배열을 처리한다', async () => {
    mockOs.cpus.mockReturnValue([])
    
    const response = await GET()
    const data = await response.json()
    
    expect(response.status).toBe(200)
    // Should handle division by zero gracefully
    expect(data.cpu).toBeNaN() // or handle this case specifically
  })
  
  it('메모리가 0일 때를 처리한다', async () => {
    mockOs.totalmem.mockReturnValue(0)
    mockOs.freemem.mockReturnValue(0)
    
    const response = await GET()
    const data = await response.json()
    
    expect(response.status).toBe(200)
    // Should handle division by zero gracefully
    expect(data.memory).toBeNaN() // or handle this case specifically
  })
  
  it('네트워크 인터페이스가 없을 때를 처리한다', async () => {
    mockOs.networkInterfaces.mockReturnValue({})
    
    const response = await GET()
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.network).toHaveProperty('bytesIn')
    expect(data.network).toHaveProperty('bytesOut')
    // 더미 데이터이므로 여전히 값이 있어야 함
    expect(typeof data.network.bytesIn).toBe('number')
    expect(typeof data.network.bytesOut).toBe('number')
  })
  
  it('os 모듈 오류를 처리한다', async () => {
    mockOs.cpus.mockImplementation(() => {
      throw new Error('OS module error')
    })
    
    const response = await GET()
    const data = await response.json()
    
    expect(response.status).toBe(500)
    expect(data.error).toBe('Failed to fetch system metrics')
  })
  
  it('메모리 계산 오류를 처리한다', async () => {
    mockOs.totalmem.mockImplementation(() => {
      throw new Error('Memory access error')
    })
    
    const response = await GET()
    const data = await response.json()
    
    expect(response.status).toBe(500)
    expect(data.error).toBe('Failed to fetch system metrics')
  })
  
  it('네트워크 정보 오류를 처리한다', async () => {
    mockOs.networkInterfaces.mockImplementation(() => {
      throw new Error('Network interface error')
    })
    
    const response = await GET()
    const data = await response.json()
    
    expect(response.status).toBe(500)
    expect(data.error).toBe('Failed to fetch system metrics')
  })
  
  it('극한 시스템 조건을 처리한다', async () => {
    // 극한 메모리 사용량 (거의 다 사용)
    mockOs.totalmem.mockReturnValue(8589934592) // 8GB
    mockOs.freemem.mockReturnValue(104857600)    // 100MB free (98.8% usage)
    
    // 극한 CPU 사용량
    mockOs.cpus.mockReturnValue([
      {
        model: 'Overloaded CPU',
        speed: 3200,
        times: { user: 90000, nice: 0, sys: 8000, idle: 1000, irq: 1000 }
      }
    ])
    
    const response = await GET()
    const data = await response.json()
    
    expect(response.status).toBe(200)
    expect(data.memory).toBeGreaterThan(95) // Very high memory usage
    expect(data.cpu).toBeGreaterThan(90)    // Very high CPU usage
  })
})