import { defineConfig } from '@apps-in-toss/web-framework/config';

export default defineConfig({
  appName: 'today-hot-topic',
  web: {
    host: 'localhost',
    port: 5173,
    commands: {
      dev: 'rsbuild dev',
      build: 'rsbuild build',
    },
  },
  permissions: [],
  outdir: 'dist',
  brand: {
    displayName: '오늘 왜 떠?',
    primaryColor: '#3182F6',
    icon: 'https://static.toss.im/appsintoss/27401/5d1d43ec-0310-45d2-a4e7-d21adbcb22a1.png',
    bridgeColorMode: 'basic',
  },
  webViewProps: {
    type: 'partner',
  },
});
