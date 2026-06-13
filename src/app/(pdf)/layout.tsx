import "./genui-site.css";

export default function GenUILandingLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return <div className="genui-site-root">{children}</div>;
}
