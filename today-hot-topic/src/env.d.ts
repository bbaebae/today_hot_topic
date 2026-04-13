/// <reference types="@rsbuild/core/types" />

interface ImportMetaEnv {
  readonly PUBLIC_USE_MOCK: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
