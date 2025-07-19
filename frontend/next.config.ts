import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  typescript: {
    // 타입 에러가 있으면 빌드 실패하도록 변경 (프로덕션 안정성)
    ignoreBuildErrors: false,
  },
  eslint: {
    // ESLint 에러가 있으면 빌드 실패하도록 변경 (코드 품질)
    ignoreDuringBuilds: false,
  },
  // 성능 최적화 설정 추가
  compress: true,
  poweredByHeader: false,
  reactStrictMode: true,
  
  // 번들 크기 최적화
  experimental: {
    optimizeCss: true,
    // 자주 사용되는 라이브러리 최적화
    optimizePackageImports: [
      '@tanstack/react-query',
      'zustand',
      'tailwindcss',
      'react-hook-form',
      'date-fns',
      'lucide-react',
    ],
  },
  
  // 이미지 최적화
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  
  // 웹팩 설정 최적화
  webpack: (config, { isServer }) => {
    // 불필요한 모듈 제외
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
      };
    }
    
    // 프로덕션 빌드 최적화
    if (process.env.NODE_ENV === 'production') {
      config.optimization = {
        ...config.optimization,
        moduleIds: 'deterministic',
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            default: false,
            vendors: false,
            // 벤더 청크 분리
            vendor: {
              name: 'vendor',
              chunks: 'all',
              test: /node_modules/,
              priority: 20,
            },
            // 공통 컴포넌트 청크
            common: {
              name: 'common',
              minChunks: 2,
              chunks: 'all',
              priority: 10,
              reuseExistingChunk: true,
              enforce: true,
            },
          },
        },
      };
    }
    
    return config;
  },
};

export default nextConfig;
