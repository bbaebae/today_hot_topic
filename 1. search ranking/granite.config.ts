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
    icon: '',
    bridgeColorMode: 'basic',
  },
  webViewProps: {
    type: 'partner',
  },
});
