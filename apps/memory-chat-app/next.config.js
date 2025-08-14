/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  transpilePackages: ['@jeanmemory/react', '@jeanmemory/node']
}

module.exports = nextConfig