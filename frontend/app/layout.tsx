import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GraphTrail - Expose Money Mule Networks",
  description:
    "Uncover hidden financial crime networks through advanced graph analytics. Detect money mule operations and trace illicit fund flows with forensic precision.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
