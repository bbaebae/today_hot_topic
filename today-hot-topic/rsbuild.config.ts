import { defineConfig } from '@rsbuild/core';
import { pluginReact } from '@rsbuild/plugin-react';

export default defineConfig({
  plugins: [pluginReact()],
  html: {
    template: './index.html',
  },
  source: {
    entry: {
      index: './src/index.tsx',
    },
    define: {
      'import.meta.env.PUBLIC_USE_MOCK': JSON.stringify(
        process.env.PUBLIC_USE_MOCK !== 'false' ? 'true' : 'false'
      ),
      'import.meta.env.PUBLIC_API_BASE_URL': JSON.stringify(
        process.env.PUBLIC_API_BASE_URL ?? 'https://todayhottopic-production.up.railway.app'
      ),
    },
  },
  server: {
    port: 5173,
    host: '0.0.0.0',  // 스마트폰에서 접근 가능하도록 모든 인터페이스에서 수신
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
