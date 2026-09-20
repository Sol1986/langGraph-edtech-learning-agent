import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Learning Agent",
  description: "Upload a PDF and learn it through an interactive quiz.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-(--color-page) text-(--color-ink)">
        {children}
      </body>
    </html>
  );
}
