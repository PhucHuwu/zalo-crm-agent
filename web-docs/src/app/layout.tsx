import type { Metadata } from "next";
import { Be_Vietnam_Pro } from "next/font/google";
import { DocsShell } from "@/components/docs-shell";
import "./globals.css";
import "./visuals.css";
import "./readability.css";

const font = Be_Vietnam_Pro({ subsets: ["latin", "vietnamese"], weight: ["400", "500", "600", "700"], variable: "--font-guide", display: "swap" });
export const metadata: Metadata = {
  title: { default: "Sổ tay Zalo OA → CRM — Cùng Claude", template: "%s | Sổ tay Zalo OA → CRM" },
  description: "Hướng dẫn từng bước dùng Claude Desktop biến hội thoại Zalo OA thành khách hàng, cơ hội, ghi chú và việc cần làm trên TinaCRM, rồi chạy chiến dịch bán hàng và chăm sóc khách. Dành cho người mới bắt đầu.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="vi"><body className={font.variable}><DocsShell>{children}</DocsShell></body></html>;
}
