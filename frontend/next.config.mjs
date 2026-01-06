/** @type {import('next').NextConfig} */
const nextConfig = {
  // Railway backend URL
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
};

export default nextConfig;

