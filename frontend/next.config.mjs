/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
      {
        protocol: "http",
        hostname: "**",
      },
    ],
  },
  // Fix for Streamdown's Shiki dependency (ES Module issue)
  // Tell Next.js to transpile streamdown and its dependencies
  // See: https://streamdown.ai/ (FAQ section)
  transpilePackages: ['streamdown', 'shiki'],
  // Additional webpack configuration to handle ES modules properly
  webpack: (config, { isServer }) => {
    // Ensure proper handling of .mjs files
    config.module.rules.push({
      test: /\.mjs$/,
      include: /node_modules/,
      type: 'javascript/auto',
    });
    
    return config;
  },
};

export default nextConfig;
