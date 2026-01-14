/**
 * 设置页面
 *
 * MVP 阶段的占位页面，为将来的设置功能预留。
 */

import { Layout, Card } from '../components';

export default function Settings() {
  return (
    <Layout>
      <div style={{
        maxWidth: '600px',
        margin: '0 auto',
        padding: '2rem',
      }}>
        <h1 style={{
          fontSize: '1.5rem',
          fontWeight: 700,
          marginBottom: '1.5rem',
        }}>
          Settings
        </h1>

        <Card title="General">
          <p style={{ color: '#999', fontSize: '0.875rem' }}>
            Settings will be available in a future update.
          </p>
        </Card>

        <div style={{ marginTop: '1rem' }}>
          <Card title="About">
            <div style={{ fontSize: '0.875rem', color: '#666' }}>
              <p><strong>KLineLens</strong></p>
              <p style={{ marginTop: '0.5rem' }}>
                Market Structure Analysis Terminal
              </p>
              <p style={{ marginTop: '0.5rem', color: '#999' }}>
                Version 0.2.0
              </p>
            </div>
          </Card>
        </div>

        <div style={{
          marginTop: '2rem',
          padding: '1rem',
          backgroundColor: '#fff3e0',
          borderRadius: '8px',
          fontSize: '0.75rem',
          color: '#ff9800',
        }}>
          <strong>Disclaimer:</strong> This tool is for educational purposes only.
          It does not provide financial advice. Always do your own research before
          making any investment decisions.
        </div>
      </div>
    </Layout>
  );
}
