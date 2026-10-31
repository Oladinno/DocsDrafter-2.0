import type { Metadata } from "next";
import { Geist, Geist_Mono, Inter } from "next/font/google";

import { AuthProvider } from "@/lib/auth";
import { ErrorReporter } from "@/components/error-reporter";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-geist",
  display: "swap",
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-geist-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "DocsDrafter - Synthesized Document Workspace",
  description:
    "Draft, refine, version and export documents with structured AI assistance.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} ${geist.variable} ${geistMono.variable} antialiased`}
      >
        <AuthProvider>
          <ErrorReporter />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
