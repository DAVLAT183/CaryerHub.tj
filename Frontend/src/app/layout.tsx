import type { Metadata } from 'next';
import { Inter, Plus_Jakarta_Sans } from 'next/font/google';
import { AuthProvider } from '@/hooks/useAuth';
import { I18nProvider } from '@/i18n/I18nContext';
import { ThemeProvider } from '@/i18n/ThemeContext';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import MiniAIChat from '@/components/chat/MiniAIChat';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
  weight: ['400', '500', '600', '700'],
});

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ['latin'],
  variable: '--font-plus-jakarta',
  display: 'swap',
  weight: ['400', '500', '600', '700'],
});

export const metadata: Metadata = {
  title: 'CareerHub // Современная платформа поиска работы',
  description: 'Найди работу или стажировку мечты. Премиальный интерфейс, умные фильтры, лучшие компании.',
  icons: {
    icon: '/favicon.svg',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={`${inter.variable} ${plusJakartaSans.variable} light`}>
      <body className="min-h-screen flex flex-col font-body bg-bg-primary text-text-primary antialiased">
          <ThemeProvider defaultTheme="light">
          <I18nProvider defaultLocale="ru">
            <AuthProvider>
              <Navbar />
              <main className="flex-1 pt-16">
                {children}
              </main>
              <Footer />
              <MiniAIChat />
            </AuthProvider>
          </I18nProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}