import { defineConfig } from 'vite'

export default defineConfig({
  // 相对路径让产物既能部署到 username.github.io，也能部署到任意仓库子路径。
  base: './',
  build: {
    target: 'es2022',
  },
})
