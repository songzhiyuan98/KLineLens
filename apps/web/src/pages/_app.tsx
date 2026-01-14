/**
 * Next.js 应用入口组件
 */

import type { AppProps } from 'next/app';
import { ErrorBoundary } from '../components';
import { I18nProvider } from '../lib/i18n';
import '../styles/globals.css';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ErrorBoundary>
      <I18nProvider>
        <Component {...pageProps} />
      </I18nProvider>
    </ErrorBoundary>
  );
}
