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
        process.env.PUBLIC_USE_MOCK === 'true' || process.env.NODE_ENV === 'development'
          ? 'true'
          : 'false'
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
