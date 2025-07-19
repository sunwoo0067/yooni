import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from '../page'

// Mock the fetch API
global.fetch = jest.fn()

// Mock the toast hook
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}))

// Mock the date picker component
jest.mock('@/components/ui/date-picker-with-range', () => ({
  DatePickerWithRange: () => null,
}))

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

describe('ERP Dashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('렌더링되고 제목이 표시된다', async () => {
    // Mock successful API response
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        data: {
          database: {
            total_size: '2.3 GB',
            table_count: 24,
            record_counts: {
              products: 156234,
              orders: 45678,
              customers: 12345,
              suppliers: 89
            },
            last_backup: '2024-01-15 03:00:00'
          },
          inventory: {
            total_products: 156234,
            total_value: 4567890000,
            low_stock: 234,
            out_of_stock: 45,
            by_market: {
              'coupang': 45678,
              'naver': 34567,
              'eleven': 23456,
              'ownerclan': 52533
            }
          },
          sales: {
            today: 3456789,
            this_week: 24567890,
            this_month: 98765432,
            growth_rate: 12.5,
            by_market: {
              'coupang': 45678900,
              'naver': 23456780,
              'eleven': 12345670,
              'ownerclan': 16985082
            }
          },
          operations: {
            pending_orders: 234,
            processing_orders: 567,
            pending_shipments: 189,
            returns_to_process: 45
          }
        }
      }),
    })
    
    render(<Dashboard />, { wrapper: createWrapper() })
    
    await waitFor(() => {
      expect(screen.getByText('ERP 통합 대시보드')).toBeInTheDocument()
    })
  })

  it('통계 카드들이 표시된다', async () => {
    const mockData = {
      success: true,
      data: {
        database: {
          total_size: '2.3 GB',
          table_count: 24,
          record_counts: {
            products: 1250,
            orders: 45,
            customers: 12345,
            suppliers: 89
          },
          last_backup: '2024-01-15 03:00:00'
        },
        inventory: {
          total_products: 1250,
          total_value: 25600000,
          low_stock: 234,
          out_of_stock: 45,
          by_market: {
            'coupang': 500,
            'naver': 300,
            'eleven': 250,
            'ownerclan': 200
          }
        },
        sales: {
          today: 15234000,
          this_week: 24567890,
          this_month: 98765432,
          growth_rate: 12.5,
          by_market: {}
        },
        operations: {
          pending_orders: 45,
          processing_orders: 567,
          pending_shipments: 189,
          returns_to_process: 45
        }
      }
    }

    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    })

    render(<Dashboard />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText('총 상품 수')).toBeInTheDocument()
      expect(screen.getByText('1,250')).toBeInTheDocument()
      expect(screen.getByText('총 주문 수')).toBeInTheDocument()
      // 여러 개의 45가 있으므로 총 주문 수 카드 내의 45를 찾음
      const orderCard = screen.getByText('총 주문 수').closest('.rounded-xl')
      expect(orderCard).toHaveTextContent('45')
    })
  })

  it('데이터베이스 통계가 표시된다', async () => {
    const mockData = {
      success: true,
      data: {
        database: {
          total_size: '2.3 GB',
          table_count: 24,
          record_counts: {
            products: 156234,
            orders: 45678,
            customers: 12345,
            suppliers: 89
          },
          last_backup: '2024-01-15 03:00:00'
        },
        inventory: {
          total_products: 156234,
          total_value: 4567890000,
          low_stock: 234,
          out_of_stock: 45,
          by_market: {}
        },
        sales: {
          today: 3456789,
          this_week: 24567890,
          this_month: 98765432,
          growth_rate: 12.5,
          by_market: {}
        },
        operations: {
          pending_orders: 234,
          processing_orders: 567,
          pending_shipments: 189,
          returns_to_process: 45
        }
      }
    }

    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    })

    render(<Dashboard />, { wrapper: createWrapper() })

    await waitFor(() => {
      expect(screen.getByText('데이터베이스')).toBeInTheDocument()
      expect(screen.getByText('2.3 GB')).toBeInTheDocument()
      expect(screen.getByText('24개 테이블')).toBeInTheDocument()
    })
  })

  it('API 오류 시 모의 데이터가 표시된다', async () => {
    ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'))

    render(<Dashboard />, { wrapper: createWrapper() })

    // API 오류 시에도 모의 데이터가 표시됨
    await waitFor(() => {
      expect(screen.getByText('ERP 통합 대시보드')).toBeInTheDocument()
      expect(screen.getByText('데이터베이스')).toBeInTheDocument()
      // 모의 데이터의 값 확인
      expect(screen.getByText('156,234')).toBeInTheDocument() // 총 상품 수
    })
  })

  it('로딩 상태가 표시된다', () => {
    ;(fetch as jest.Mock).mockImplementation(() => 
      new Promise(() => {}) // Never resolves
    )

    render(<Dashboard />, { wrapper: createWrapper() })

    expect(screen.getByText(/로딩 중/)).toBeInTheDocument()
  })
})