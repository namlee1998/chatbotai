const fetch = require('node-fetch');

test('Đăng nhập trả về token', async () => {
  const response = await fetch('http://127.0.0.1:8080/api/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: new URLSearchParams({
      username: 'admin',
      password: 'Namltmta1998'  // nếu đây là mật khẩu thật của user giả trong backend
    }).toString()
  });

  expect(response.status).toBe(200);
  const data = await response.json();
  expect(data.access_token).toBeDefined();  // ✅ đúng trường
});
