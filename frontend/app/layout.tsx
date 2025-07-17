import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import QueryProvider from "@/components/providers/QueryProvider";

export const metadata: Metadata = {
  title: "ERP System",
  description: "통합 이커머스 관리 시스템",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className="antialiased">
        <QueryProvider>
          <Sidebar />
          <Header />
          <main className="ml-64 mt-16 min-h-screen bg-gray-50">
            {children}
          </main>
        </QueryProvider>
      </body>
    </html>
  );
}