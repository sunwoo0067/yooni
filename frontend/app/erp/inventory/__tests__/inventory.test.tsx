import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import InventoryPage from '../page'

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

describe('재고 관리 페이지', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  const mockInventoryData = {
    items: [
      {
        id: 1,
        product_name: '테스트 상품 1',
        sku: 'SKU001',
        current_stock: 100,
        safety_stock: 20,
        location: 'A-1-1',
        last_updated: '2024-01-15T10:00:00'
      },
      {
        id: 2,
        product_name: '테스트 상품 2',
        sku: 'SKU002',
        current_stock: 15,
        safety_stock: 30,
        location: 'B-2-3',
        last_updated: '2024-01-15T11:00:00'
      }
    ],
    total: 2,
    page: 1,
    pageSize: 20
  }

  it('재고 목록이 표시된다', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockInventoryData,
    })

    render(<InventoryPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText('재고 관리')).toBeInTheDocument()
      expect(screen.getByText('테스트 상품 1')).toBeInTheDocument()
      expect(screen.getByText('SKU001')).toBeInTheDocument()
      expect(screen.getByText('100')).toBeInTheDocument()
    })
  })

  it('안전재고 미달 항목이 강조 표시된다', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockInventoryData,
    })

    render(<InventoryPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      const lowStockItem = screen.getByText('테스트 상품 2').closest('tr')
      expect(lowStockItem).toHaveClass('bg-red-50')
    })
  })

  it('검색 기능이 동작한다', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockInventoryData,
    })

    render(<InventoryPage />, { wrapper: createWrapper() })

    const searchInput = screen.getByPlaceholderText('상품명, SKU로 검색')
    fireEvent.change(searchInput, { target: { value: 'SKU001' } })

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('search=SKU001')
      )
    })
  })

  it('재고 조정 버튼이 동작한다', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockInventoryData,
    })

    render(<InventoryPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      const adjustButton = screen.getAllByText('조정')[0]
      fireEvent.click(adjustButton)
      
      expect(screen.getByText('재고 조정')).toBeInTheDocument()
      expect(screen.getByLabelText('조정 수량')).toBeInTheDocument()
    })
  })

  it('페이지네이션이 동작한다', async () => {
    const multiPageData = {
      ...mockInventoryData,
      total: 50,
      pageSize: 20
    }

    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => multiPageData,
    })

    render(<InventoryPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      const nextButton = screen.getByText('다음')
      fireEvent.click(nextButton)
      
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('page=2')
      )
    })
  })

  it('필터가 동작한다', async () => {
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockInventoryData,
    })

    render(<InventoryPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      const filterButton = screen.getByText('재고 부족')
      fireEvent.click(filterButton)
      
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('stockStatus=low')
      )
    })
  })

  it('에러 상태가 표시된다', async () => {
    ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'))

    render(<InventoryPage />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText(/재고 데이터를 불러오는데 실패했습니다/)).toBeInTheDocument()
    })
  })
})