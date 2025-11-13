import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Dashboard Ejecutivo - Comversa',
  description: 'Análisis consolidado de inteligencia empresarial de 44 entrevistas',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className="antialiased bg-[#F5F5F5]">{children}</body>
    </html>
  );
}
