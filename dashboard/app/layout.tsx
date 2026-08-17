import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Fred Bot Dashboard",
  description: "Live backtest results for the FredbV2 Freqtrade strategy.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
          background: "#0b0d12",
          color: "#e6e9ef",
        }}
      >
        {children}
      </body>
    </html>
  );
}
