// api/get-api-url.js

export default function handler(request, response) {
  // 这个函数会读取 Vercel 的环境变量
  const apiUrl = process.env.API_URL;

  if (!apiUrl) {
    return response.status(500).json({ error: 'API URL is not configured on the server.' });
  }

  // 它将 API URL 以 JSON 格式返回给前端
  response.status(200).json({ apiUrl });
}