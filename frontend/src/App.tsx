import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import ChatPage from "./ChatPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
