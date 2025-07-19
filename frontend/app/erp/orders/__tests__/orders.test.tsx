import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import OrdersPage from '../page'

// Mock the fetch API
global.fetch = jest.fn()

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('주문 관리 페이지', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  const mockOrdersData = {
    orders: [
      {
        id: 1,
        order_id: 'ORD-2024-0001',
        customer_name: '홍길동',
        order_date: '2024-01-15T10:00:00',
        total_amount: 150000,
        status: 'pending',
        item_count: 3,
        shipping_address: '서울시 강남구 테스트로 123'
      },
      {
        id: 2,
        order_id: 'ORD-2024-0002',
        customer_name: '김철수',
        order_date: '2024-01-15T14:30:00',
        total_amount: 75000,
        status: 'processing',
        item_count: 1,
        shipping_address: '부산시 해운대구 샘플로 456'
      }
    ],
    total: 2,
    page: 1,
    pageSize: 20
  }

  it('주문 목록이 표시된다', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockOrdersData,
    })

    render(<OrdersPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText('주문 관리')).toBeInTheDocument()
      expect(screen.getByText('ORD-2024-0001')).toBeInTheDocument()
      expect(screen.getByText('홍길동')).toBeInTheDocument()
      expect(screen.getByText('₩150,000')).toBeInTheDocument()
    })
  })

  it('주문 상태별로 스타일이 다르게 표시된다', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockOrdersData,
    })

    render(<OrdersPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      const pendingStatus = screen.getByText('대기중')
      const processingStatus = screen.getByText('처리중')
      
      expect(pendingStatus).toHaveClass('bg-yellow-100')
      expect(processingStatus).toHaveClass('bg-blue-100')
    })
  })

  it('주문 상세 보기가 동작한다', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockOrdersData,
    })

    render(<OrdersPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      const detailButton = screen.getAllByText('상세')[0]
      fireEvent.click(detailButton)
      
      expect(screen.getByText('주문 상세 정보')).toBeInTheDocument()
      expect(screen.getByText('배송 주소:')).toBeInTheDocument()
    })
  })

  it('주문 상태 필터가 동작한다', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockOrdersData,
    })

    render(<OrdersPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      const filterSelect = screen.getByLabelText('상태 필터')
      fireEvent.change(filterSelect, { target: { value: 'pending' } })
      
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('status=pending')
      )
    })
  })

  it('날짜 범위 필터가 동작한다', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockOrdersData,
    })

    render(<OrdersPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      const startDateInput = screen.getByLabelText('시작일')
      const endDateInput = screen.getByLabelText('종료일')
      
      fireEvent.change(startDateInput, { target: { value: '2024-01-01' } })
      fireEvent.change(endDateInput, { target: { value: '2024-01-31' } })
      
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('startDate=2024-01-01')
      )
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('endDate=2024-01-31')
      )
    })
  })

  it('주문 상태 변경이 동작한다', async () => {
    ;(fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockOrdersData,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      })

    render(<OrdersPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      const statusButton = screen.getAllByText('상태 변경')[0]
      fireEvent.click(statusButton)
      
      const confirmButton = screen.getByText('배송중으로 변경')
      fireEvent.click(confirmButton)
    })

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/erp/orders/1/status'),
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({ status: 'shipping' })
        })
      )
    })
  })

  it('검색 기능이 동작한다', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockOrdersData,
    })

    render(<OrdersPage />, { wrapper: createWrapper() })

    const searchInput = screen.getByPlaceholderText('주문번호, 고객명으로 검색')
    fireEvent.change(searchInput, { target: { value: 'ORD-2024' } })

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('search=ORD-2024')
      )
    })
  })

  it('주문 데이터가 없을 때 메시지가 표시된다', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ orders: [], total: 0 }),
    })

    render(<OrdersPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText('주문 내역이 없습니다')).toBeInTheDocument()
    })
  })
})