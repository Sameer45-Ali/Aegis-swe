import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aegis-SWE Cockpit | Autonomous Coding Agent",
  description: "Autonomous SWE Agent with Monte Carlo Tree Search, AST Code Graph, and Sandboxed Execution.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090d16] text-gray-100 min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}