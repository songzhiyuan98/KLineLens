/**
 * 设置页面
 */

import { Layout, Card } from '../components';
import { useI18n, Language } from '../lib/i18n';

const styles = {
  container: {
    maxWidth: '600px',
    margin: '0 auto',
    padding: '2rem',
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: 700,
    marginBottom: '1.5rem',
  },
  section: {
    marginTop: '1rem',
  },
  settingRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.75rem 0',
    borderBottom: '1px solid #eaeaea',
  },
  settingLabel: {
    fontSize: '0.875rem',
    color: '#333',
  },
  langToggle: {
    display: 'flex',
    gap: '4px',
  },
  langButton: {
    padding: '0.375rem 0.75rem',
    border: '1px solid #eaeaea',
    borderRadius: '4px',
    fontSize: '0.75rem',
    cursor: 'pointer',
    backgroundColor: 'transparent',
    color: '#666',
    transition: 'all 0.2s',
  },
  langButtonActive: {
    backgroundColor: '#26a69a',
    borderColor: '#26a69a',
    color: '#fff',
  },
  disclaimer: {
    marginTop: '2rem',
    padding: '1rem',
    backgroundColor: '#fff3e0',
    borderRadius: '8px',
    fontSize: '0.75rem',
    color: '#ff9800',
  },
  infoText: {
    color: '#999',
    fontSize: '0.875rem',
  },
  aboutInfo: {
    fontSize: '0.875rem',
    color: '#666',
  },
};

export default function Settings() {
  const { lang, setLang, t } = useI18n();

  const handleLangChange = (newLang: Language) => {
    setLang(newLang);
  };

  return (
    <Layout>
      <div style={styles.container}>
        <h1 style={styles.title}>{t('settings')}</h1>

        <Card title={t('general')}>
          <div style={styles.settingRow}>
            <span style={styles.settingLabel}>{t('language')}</span>
            <div style={styles.langToggle}>
              <button
                onClick={() => handleLangChange('zh')}
                style={{
                  ...styles.langButton,
                  ...(lang === 'zh' ? styles.langButtonActive : {}),
                }}
              >
                {t('chinese')}
              </button>
              <button
                onClick={() => handleLangChange('en')}
                style={{
                  ...styles.langButton,
                  ...(lang === 'en' ? styles.langButtonActive : {}),
                }}
              >
                {t('english')}
              </button>
            </div>
          </div>
          <p style={{ ...styles.infoText, marginTop: '1rem' }}>
            {t('settings_future')}
          </p>
        </Card>

        <div style={styles.section}>
          <Card title={t('about')}>
            <div style={styles.aboutInfo}>
              <p><strong>KLineLens</strong></p>
              <p style={{ marginTop: '0.5rem' }}>
                {t('app_description')}
              </p>
              <p style={{ marginTop: '0.5rem', color: '#999' }}>
                {t('version')} 0.2.0
              </p>
            </div>
          </Card>
        </div>

        <div style={styles.disclaimer}>
          <strong>{t('disclaimer')}:</strong> {t('disclaimer_text')}
        </div>
      </div>
    </Layout>
  );
}
