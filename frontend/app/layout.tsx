import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Integration Scout",
  description: "Find companies that need integrations built — evidence-first GTM pipeline.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
