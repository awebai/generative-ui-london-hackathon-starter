import { Plus_Jakarta_Sans, Spline_Sans_Mono } from "next/font/google";
import "@/a2ui/theme.css";
import "../(pdf)/pdf-analyst.css";

const plusJakarta = Plus_Jakarta_Sans({
  variable: "--font-plus-jakarta",
  subsets: ["latin"],
  display: "swap",
});

const splineMono = Spline_Sans_Mono({
  variable: "--font-spline-mono",
  subsets: ["latin"],
  display: "swap",
});

export default function PresentLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <div
      className={`pdf-analyst-root ${plusJakarta.variable} ${splineMono.variable} antialiased min-h-screen`}
    >
      {children}
    </div>
  );
}
