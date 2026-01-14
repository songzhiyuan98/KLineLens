/**
 * Next.js 应用入口组件
 *
 * 这是 Next.js 的自定义 App 组件，用于初始化页面。
 * 所有页面都会通过这个组件渲染。
 *
 * 功能:
 * - 页面布局包装
 * - 全局样式应用
 */

import type { AppProps } from 'next/app';
import '../styles/globals.css';

/**
 * 根应用组件
 *
 * @param Component - 当前页面组件
 * @param pageProps - 页面属性
 * @returns 渲染的页面
 */
export default function App({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />;
}
