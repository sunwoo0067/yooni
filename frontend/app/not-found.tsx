import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function NotFound() {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-center">
        <h2 className="text-4xl font-bold mb-4">404</h2>
        <h3 className="text-2xl font-semibold mb-2">페이지를 찾을 수 없습니다</h3>
        <p className="text-gray-600 mb-6">
          요청하신 페이지가 존재하지 않거나 이동되었습니다.
        </p>
        <Link href="/">
          <Button className="bg-blue-500 hover:bg-blue-600 text-white">
            홈으로 돌아가기
          </Button>
        </Link>
      </div>
    </div>
  );
}