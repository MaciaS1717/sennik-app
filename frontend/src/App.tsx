import { Routes, Route, Navigate } from "react-router-dom"
import HomePage from "./pages/HomePage.tsx"
import LoginPage from "./pages/LoginPage.tsx"
import RegisterPage from "./pages/RegisterPage.tsx"

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
