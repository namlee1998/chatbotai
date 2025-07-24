const fetch = require('node-fetch');

test('Đăng nhập trả về token', async () => {
  const response = await fetch('http://127.0.0.1:8080/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: '123456' })
  });

  expect(response.status).toBe(200);
  const data = await response.json();
  expect(data.token).toBeDefined();
});
