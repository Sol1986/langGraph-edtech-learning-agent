import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

import { CopilotProvider } from "@/components/CopilotProvider";

const openSans = localFont({
  src: "./fonts/OpenSans-Variable.ttf",
  variable: "--font-open-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AI Learning Agent",
  description: "Upload a PDF and learn it through an interactive quiz.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${openSans.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <CopilotProvider>{children}</CopilotProvider>
      </body>
    </html>
  );
}
