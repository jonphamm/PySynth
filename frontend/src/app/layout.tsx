import type { Metadata, Viewport } from "next";
import { Geist, Fira_Code } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const firaCode = Fira_Code({
  variable: "--font-fira-code",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "PySynth — Python Tutor",
  description:
    "PySynth is a futuristic Python learning environment. Concept review, quiz, code, grade — guided.",
  // apple-touch-icon is required for the "Add to Home Screen" install on iOS;
  // without it, iOS uses a screenshot of the page as the icon.
  icons: {
    apple: "/apple-touch-icon.png",
  },
  // Marks the page as a fullscreen PWA on iOS once installed to home screen.
  // Status bar style "black-translucent" lets our dark theme bleed into the
  // top status area.
  appleWebApp: {
    capable: true,
    title: "PySynth",
    statusBarStyle: "black-translucent",
  },
};

export const viewport: Viewport = {
  themeColor: "#020203",
  width: "device-width",
  initialScale: 1,
  // Lock zoom inside the PWA shell so it doesn't behave like a webpage.
  userScalable: false,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${firaCode.variable} h-full antialiased`}
    >
      <body className="min-h-full">{children}</body>
    </html>
  );
}
