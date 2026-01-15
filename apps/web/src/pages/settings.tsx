/**
 * 设置页面 - 简洁现代风格
 */

import { Layout } from '../components';
import { useI18n, Language } from '../lib/i18n';

// Fluid typography
const F = {
  small: 'clamp(0.75rem, 0.65rem + 0.2vw, 0.875rem)',
  body: 'clamp(0.875rem, 0.75rem + 0.25vw, 1rem)',
  heading: 'clamp(1.25rem, 1rem + 0.5vw, 1.5rem)',
};

const MONO = '"SF Mono", "Roboto Mono", "Fira Code", Menlo, Monaco, monospace';

export default function Settings() {
  const { lang, setLang, t } = useI18n();

  return (
    <Layout>
      <div style={{
        maxWidth: '560px',
        margin: '0 auto',
        padding: 'clamp(1.5rem, 4vw, 3rem) clamp(1rem, 3vw, 2rem)',
      }}>
        {/* Header */}
        <h1 style={{
          fontSize: F.heading,
          fontWeight: 600,
          marginBottom: 'clamp(2rem, 4vw, 3rem)',
          color: '#000',
        }}>
          {t('settings')}
        </h1>

        {/* Language Setting */}
        <section style={{ marginBottom: '2.5rem' }}>
          <div style={{
            fontSize: 'clamp(0.625rem, 0.5rem + 0.2vw, 0.75rem)',
            fontWeight: 500,
            color: '#999',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginBottom: '0.75rem',
          }}>
            {t('language')}
          </div>

          <div style={{
            display: 'flex',
            gap: '0.5rem',
          }}>
            {(['zh', 'en'] as Language[]).map((l) => (
              <button
                key={l}
                onClick={() => setLang(l)}
                style={{
                  padding: '0.625rem 1.25rem',
                  fontSize: F.small,
                  fontWeight: 500,
                  border: '1px solid',
                  borderColor: lang === l ? '#000' : '#e5e5e5',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  backgroundColor: lang === l ? '#000' : '#fff',
                  color: lang === l ? '#fff' : '#666',
                  transition: 'all 0.15s',
                }}
              >
                {l === 'zh' ? '中文' : 'English'}
              </button>
            ))}
          </div>
        </section>

        {/* About */}
        <section style={{ marginBottom: '2.5rem' }}>
          <div style={{
            fontSize: 'clamp(0.625rem, 0.5rem + 0.2vw, 0.75rem)',
            fontWeight: 500,
            color: '#999',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginBottom: '0.75rem',
          }}>
            {t('about')}
          </div>

          <div style={{
            padding: '1rem 1.25rem',
            backgroundColor: '#fafafa',
            borderRadius: '8px',
            border: '1px solid #f0f0f0',
          }}>
            <div style={{
              fontSize: F.body,
              fontWeight: 600,
              color: '#000',
              marginBottom: '0.375rem',
            }}>
              KLineLens
            </div>
            <div style={{
              fontSize: F.small,
              color: '#666',
              marginBottom: '0.5rem',
            }}>
              {t('app_description')}
            </div>
            <div style={{
              fontSize: F.small,
              fontFamily: MONO,
              color: '#999',
            }}>
              v0.2.0
            </div>
          </div>
        </section>

        {/* Disclaimer */}
        <section>
          <div style={{
            fontSize: 'clamp(0.625rem, 0.5rem + 0.2vw, 0.75rem)',
            fontWeight: 500,
            color: '#999',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginBottom: '0.75rem',
          }}>
            {t('disclaimer')}
          </div>

          <div style={{
            fontSize: F.small,
            lineHeight: 1.6,
            color: '#666',
            padding: '1rem 1.25rem',
            backgroundColor: '#fff',
            borderRadius: '8px',
            border: '1px solid #e5e5e5',
          }}>
            {t('disclaimer_text')}
          </div>
        </section>
      </div>
    </Layout>
  );
}
