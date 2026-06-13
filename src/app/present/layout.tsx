import "@/a2ui/theme.css";
import "../(pdf)/genui-site.css";

export default function PresentLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return <div className="genui-present-root">{children}</div>;
}
