import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Synapsis",
  description: "Your personal, air-gapped knowledge engine",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
