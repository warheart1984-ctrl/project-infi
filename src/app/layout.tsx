import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'AAIS Starter',
  description: 'Adaptive Autonomous Intelligence System starter project',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
