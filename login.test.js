const fetch = require('node-fetch');

test('Đăng nhập trả về token', async () => {
  const response = await fetch('http://localhost:8080/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: 'Namltmta1998' })
  });

  expect(response.status).toBe(200);
  const data = await response.json();
  expect(data.token).toBeDefined();
});
