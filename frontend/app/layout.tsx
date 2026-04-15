import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/src/components/nav/Navbar";
import { Providers } from "@/src/components/Providers";

export const metadata: Metadata = {
  title: "KantoVision",
  description: "Pokédex · Team Builder · AI Scanner",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="noise">
      <body className="bg-grid min-h-screen" style={{ backgroundSize: "40px 40px" }}>
        <Providers>
          <Navbar />
          <main className="pt-16">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
