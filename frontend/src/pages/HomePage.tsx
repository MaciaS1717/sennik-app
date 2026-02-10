import { Link } from "react-router-dom"

export default function HomePage() {
  return (
    <div style={{ padding: 16 }}>
      <h1>Home</h1>
      <p>
        <Link to="/morning">Dodaj poranny raport</Link>
      </p>
      <p>
        <Link to="/evening">Dodaj wieczorny raport</Link>
      </p>
    </div>
  )
}
