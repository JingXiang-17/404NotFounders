import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import QueryProvider from "@/components/QueryProvider";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "LintasNiaga",
  description: "LintasNiaga compares FOB PP Resin quotes, simulates FX scenarios, and recommends the best-value supplier for Malaysian importers.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} dark antialiased h-full`}>
      <body className="min-h-full flex flex-col font-sans bg-background text-foreground">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
