import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Homework Crawler",
  description: "FastCampus LMS 과제 수집기",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gray-50 text-gray-900">{children}</body>
    </html>
  );
}
