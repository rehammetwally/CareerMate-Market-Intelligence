const config = {
  apiUrl: process.env.REACT_APP_API_URL || 'http://localhost:8001',
};

export const apiUrl = config.apiUrl;
export default config;