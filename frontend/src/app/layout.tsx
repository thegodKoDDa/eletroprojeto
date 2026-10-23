import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {
  title: 'EletroProjeto · Cargas residenciais',
  description: 'Cálculos elétricos com memória e rastreabilidade.',
};
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
