import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Fred Bot Dashboard",
  description: "Live backtest results for the FredbV2 Freqtrade strategy.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
