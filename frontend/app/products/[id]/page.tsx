'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useProduct, useUpdateProduct } from '@/lib/hooks/useProduct';
import { SUPPLIERS } from '@/lib/types/product';
import { ArrowLeft, Edit2, Save, X, Package, Truck, DollarSign, AlertCircle } from 'lucide-react';

export default function ProductDetailPage() {
  const params = useParams();
  const router = useRouter();
  const productId = params.id as string;
  
  const { data: product, isLoading, error } = useProduct(productId);
  const updateProduct = useUpdateProduct(productId);
  
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    product_name: '',
    brand: '',
    manufacturer: '',
    origin: '',
    category: '',
    status: '',
    price: 0,
    list_price: 0,
    shipping_fee: 0,
    stock_quantity: 0,
    description: '',
  });

  const startEdit = () => {
    if (product) {
      setEditForm({
        product_name: product.product_name || '',
        brand: product.brand || '',
        manufacturer: product.manufacturer || '',
        origin: product.origin || '',
        category: product.category || '',
        status: product.status || '',
        price: product.price || 0,
        list_price: product.list_price || 0,
        shipping_fee: product.shipping_fee || 0,
        stock_quantity: product.stock_quantity || 0,
        description: product.description || '',
      });
      setIsEditing(true);
    }
  };

  const cancelEdit = () => {
    setIsEditing(false);
    setEditForm({
      product_name: '',
      brand: '',
      manufacturer: '',
      origin: '',
      category: '',
      status: '',
      price: 0,
      list_price: 0,
      shipping_fee: 0,
      stock_quantity: 0,
      description: '',
    });
  };

  const saveEdit = async () => {
    try {
      await updateProduct.mutateAsync(editForm);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update product:', error);
    }
  };

  const formatPrice = (price: number | null) => {
    if (!price) return '0원';
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
    }).format(price);
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      soldout: 'bg-red-100 text-red-800',
      available: 'bg-blue-100 text-blue-800',
    };
    
    const labels = {
      active: '활성',
      inactive: '비활성',
      soldout: '품절',
      available: '판매가능',
    };

    return (
      <span className={`px-3 py-1 text-sm font-medium rounded-full ${styles[status as keyof typeof styles] || ''}`}>
        {labels[status as keyof typeof labels] || status}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">로딩 중...</div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          상품을 불러오는 중 오류가 발생했습니다.
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* 헤더 */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/products')}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-2xl font-bold">상품 상세 정보</h1>
              <p className="text-gray-600 mt-1">#{product.supplier_product_id}</p>
            </div>
          </div>
          <div className="flex gap-2">
            {!isEditing ? (
              <button
                onClick={startEdit}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
              >
                <Edit2 size={16} />
                수정
              </button>
            ) : (
              <>
                <button
                  onClick={saveEdit}
                  disabled={updateProduct.isPending}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2 disabled:opacity-50"
                >
                  <Save size={16} />
                  저장
                </button>
                <button
                  onClick={cancelEdit}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
                >
                  <X size={16} />
                  취소
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 왼쪽: 이미지 및 기본 정보 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 이미지 영역 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">상품 이미지</h2>
            <div className="grid grid-cols-4 gap-4">
              {product.images && product.images.length > 0 ? (
                product.images.slice(0, 8).map((image, index) => (
                  <div key={index} className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
                    <img src={image} alt={`상품 이미지 ${index + 1}`} className="w-full h-full object-cover" />
                  </div>
                ))
              ) : (
                <div className="col-span-4 h-64 bg-gray-100 rounded-lg flex items-center justify-center">
                  <Package size={48} className="text-gray-400" />
                </div>
              )}
            </div>
          </div>

          {/* 상품 정보 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">상품 정보</h2>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">상품명</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={editForm.product_name}
                    onChange={(e) => setEditForm({ ...editForm, product_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">{product.product_name}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">브랜드</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={editForm.brand}
                    onChange={(e) => setEditForm({ ...editForm, brand: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">{product.brand || '-'}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">제조사</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={editForm.manufacturer}
                    onChange={(e) => setEditForm({ ...editForm, manufacturer: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">{product.manufacturer || '-'}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">원산지</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={editForm.origin}
                    onChange={(e) => setEditForm({ ...editForm, origin: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">{product.origin || '-'}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">카테고리</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={editForm.category}
                    onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">{product.category || '-'}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">상태</label>
                {isEditing ? (
                  <select
                    value={editForm.status}
                    onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                  >
                    <option value="active">활성</option>
                    <option value="available">판매가능</option>
                    <option value="inactive">비활성</option>
                    <option value="soldout">품절</option>
                  </select>
                ) : (
                  <div>{getStatusBadge(product.status)}</div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 오른쪽: 가격 및 재고 정보 */}
        <div className="space-y-6">
          {/* 공급업체 정보 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">공급업체</h2>
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Package size={24} className="text-blue-600" />
              </div>
              <div>
                <p className="font-medium">{SUPPLIERS[product.supplier_id]?.name}</p>
                <p className="text-sm text-gray-500">ID: {product.supplier_product_id}</p>
              </div>
            </div>
          </div>

          {/* 가격 정보 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">가격 정보</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">판매가</label>
                {isEditing ? (
                  <input
                    type="number"
                    value={editForm.price}
                    onChange={(e) => setEditForm({ ...editForm, price: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                ) : (
                  <p className="text-2xl font-bold text-blue-600">{formatPrice(product.price)}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">정가</label>
                {isEditing ? (
                  <input
                    type="number"
                    value={editForm.list_price}
                    onChange={(e) => setEditForm({ ...editForm, list_price: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                ) : (
                  <p className="text-lg text-gray-500 line-through">{formatPrice(product.list_price)}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">배송비</label>
                {isEditing ? (
                  <input
                    type="number"
                    value={editForm.shipping_fee}
                    onChange={(e) => setEditForm({ ...editForm, shipping_fee: Number(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">{formatPrice(product.shipping_fee)}</p>
                )}
              </div>
              
              {product.list_price && product.price && product.list_price > product.price && (
                <div className="pt-4 border-t">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">할인율</span>
                    <span className="text-sm font-medium text-red-600">
                      {Math.round((1 - product.price / product.list_price) * 100)}%
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 재고 정보 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">재고 정보</h2>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">재고 수량</label>
              {isEditing ? (
                <input
                  type="number"
                  value={editForm.stock_quantity}
                  onChange={(e) => setEditForm({ ...editForm, stock_quantity: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                />
              ) : (
                <div className="flex items-center gap-2">
                  <p className="text-2xl font-bold">{product.stock_quantity || 0}</p>
                  <span className="text-gray-500">개</span>
                </div>
              )}
              
              {product.stock_quantity !== null && product.stock_quantity < 10 && (
                <div className="mt-2 flex items-center gap-2 text-amber-600">
                  <AlertCircle size={16} />
                  <span className="text-sm">재고 부족 주의</span>
                </div>
              )}
            </div>
          </div>

          {/* 등록 정보 */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">등록 정보</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">등록일</span>
                <span>{new Date(product.created_at).toLocaleDateString('ko-KR')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">수정일</span>
                <span>{new Date(product.updated_at).toLocaleDateString('ko-KR')}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}