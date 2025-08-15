import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Homework Crawler",
  description: "FastCampus LMS 과제 수집기",
  icons: {
    icon: "/favicon.png",
    shortcut: "/favicon.png",
    apple: "/favicon.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gradient-to-b from-pink-50 to-white text-gray-900 antialiased dark:from-neutral-900 dark:to-neutral-950">
        {children}
      </body>
    </html>
  );
}
