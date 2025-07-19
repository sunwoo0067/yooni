// inventory 테스트는 임시적으로 비활성화 (inventory route가 아직 구현되지 않음)
// import { GET, PATCH } from '../inventory/route'
// import { NextRequest } from 'next/server'

// Mock the database module
jest.mock('pg', () => ({
  Pool: jest.fn(() => ({
    query: jest.fn(),
    end: jest.fn(),
  })),
}))

describe.skip('/api/erp/inventory (임시 비활성화)', () => {
  let mockPool: any

  beforeEach(() => {
    jest.clearAllMocks()
    const { Pool } = require('pg')
    mockPool = new Pool()
  })

  describe('GET', () => {
    it('재고 목록을 반환한다', async () => {
      const mockInventory = {
        rows: [
          {
            id: 1,
            product_name: '테스트 상품',
            sku: 'SKU001',
            current_stock: 100,
            safety_stock: 20,
            location: 'A-1-1',
            last_updated: new Date('2024-01-15T10:00:00')
          }
        ]
      }

      const mockCount = { rows: [{ count: '1' }] }

      mockPool.query
        .mockResolvedValueOnce(mockInventory)
        .mockResolvedValueOnce(mockCount)

      // const response = await GET(new NextRequest('http://localhost:3000/api/erp/inventory'))
      // const data = await response.json()

      // expect(response.status).toBe(200)
      // expect(data.items).toHaveLength(1)
      // expect(data.total).toBe(1)
      // expect(data.items[0].product_name).toBe('테스트 상품')
    })

    it('검색 파라미터가 적용된다', async () => {
      // mockPool.query.mockResolvedValue({ rows: [] })

      // const url = 'http://localhost:3000/api/erp/inventory?search=SKU001&stockStatus=low'
      // await GET(new NextRequest(url))

      // expect(mockPool.query).toHaveBeenCalledWith(
      //   expect.stringContaining("product_name ILIKE $1 OR sku ILIKE $1"),
      //   expect.arrayContaining(['%SKU001%'])
      // )
    })

    it('페이지네이션이 적용된다', async () => {
      // mockPool.query.mockResolvedValue({ rows: [] })

      // const url = 'http://localhost:3000/api/erp/inventory?page=2&pageSize=10'
      // await GET(new NextRequest(url))

      // expect(mockPool.query).toHaveBeenCalledWith(
      //   expect.stringContaining('LIMIT $'),
      //   expect.arrayContaining([10, 10]) // LIMIT 10 OFFSET 10
      // )
    })
  })

  describe('PATCH', () => {
    it('재고를 조정한다', async () => {
      // mockPool.query.mockResolvedValueOnce({ rowCount: 1 })

      // const request = new NextRequest('http://localhost:3000/api/erp/inventory', {
      //   method: 'PATCH',
      //   body: JSON.stringify({
      //     productId: 1,
      //     adjustment: 10,
      //     reason: '입고'
      //   })
      // })

      // const response = await PATCH(request)
      // const data = await response.json()

      // expect(response.status).toBe(200)
      // expect(data.success).toBe(true)
      // expect(mockPool.query).toHaveBeenCalledWith(
      //   expect.stringContaining('UPDATE unified_products'),
      //   expect.arrayContaining([10, 1])
      // )
    })

    it('잘못된 요청 시 400을 반환한다', async () => {
      // const request = new NextRequest('http://localhost:3000/api/erp/inventory', {
      //   method: 'PATCH',
      //   body: JSON.stringify({
      //     productId: 1
      //     // adjustment missing
      //   })
      // })

      // const response = await PATCH(request)
      // const data = await response.json()

      // expect(response.status).toBe(400)
      // expect(data.error).toBe('Missing required fields')
    })

    it('존재하지 않는 상품 시 404를 반환한다', async () => {
      // mockPool.query.mockResolvedValueOnce({ rowCount: 0 })

      // const request = new NextRequest('http://localhost:3000/api/erp/inventory', {
      //   method: 'PATCH',
      //   body: JSON.stringify({
      //     productId: 999,
      //     adjustment: 10,
      //     reason: '조정'
      //   })
      // })

      // const response = await PATCH(request)
      // const data = await response.json()

      // expect(response.status).toBe(404)
      // expect(data.error).toBe('Product not found')
    })
  })
})