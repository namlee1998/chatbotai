const fetch = require('node-fetch');

test('Chatbot phản hồi đúng với câu hỏi đơn giản', async () => {
  const response = await fetch('http://127.0.0.1:8080/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: 'How are you?' })
  });

  expect(response.status).toBe(200);
  const data = await response.json();
  expect(data.reply).toMatch(/(I'm fine.Thanks you)/i);
});
