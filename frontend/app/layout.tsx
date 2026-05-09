import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Rutter Integration Radar",
  description: "Evidence-first GTM pipeline for integration-heavy companies",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
