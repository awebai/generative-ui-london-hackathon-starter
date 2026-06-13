import "./globals.css";

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <title>atext.ai — agent-first generative UI</title>
        <link rel="icon" type="image/svg+xml" href="/copilotkit-logo-mark.svg" />
      </head>
      <body>{children}</body>
    </html>
  );
}
