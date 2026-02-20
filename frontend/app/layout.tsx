import type { Metadata } from "next";
import { Abhaya_Libre, Bricolage_Grotesque } from "next/font/google";
import "./globals.css";

const abhayaLibre = Abhaya_Libre({
  subsets: ["latin"],
  weight: ["800"],
  variable: "--font-heading",
});

const bricolageGrotesque = Bricolage_Grotesque({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-subheading",
});

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
      <body className={`${abhayaLibre.variable} ${bricolageGrotesque.variable} antialiased`}>{children}</body>
    </html>
  );
}
