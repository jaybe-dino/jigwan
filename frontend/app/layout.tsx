import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "지관 — 터를 봐드립니다",
  description: "주소를 넣으면 AI가 실제 지형·도로·건물 데이터로 그 터의 풍수를 감정합니다.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <main className="phone">{children}</main>
      </body>
    </html>
  );
}
