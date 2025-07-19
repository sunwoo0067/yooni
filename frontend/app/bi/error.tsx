'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';

export default function BIError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('BI Dashboard Error:', error);
  }, [error]);

  return (
    <div className="container mx-auto p-6">
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <AlertCircle className="h-16 w-16 text-red-500 mb-4" />
        <h2 className="text-2xl font-bold mb-2">BI 대시보드 오류</h2>
        <p className="text-gray-600 mb-6 text-center max-w-md">
          비즈니스 인텔리전스 데이터를 불러오는 중 문제가 발생했습니다.
          <br />
          API 서버가 실행 중인지 확인해주세요.
        </p>
        <div className="space-x-4">
          <Button
            onClick={() => reset()}
            className="bg-blue-500 hover:bg-blue-600 text-white"
          >
            다시 시도
          </Button>
          <Button
            variant="outline"
            onClick={() => window.location.href = '/'}
          >
            홈으로 이동
          </Button>
        </div>
      </div>
    </div>
  );
}