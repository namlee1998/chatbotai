// src/app/layout.tsx
import "./globals.css";
import { Inter } from "next/font/google";
import type { Metadata } from "next";

const font = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Chatbot UI",
  description: "Your AI assistant",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={font.className}>{children}</body>
    </html>
  );
}
