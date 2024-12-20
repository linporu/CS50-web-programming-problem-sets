import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user } = useAuth();

  return (
    <div>
      <nav className="bg-gray-100 p-4">
        <h1>Network</h1>
        <div className="space-x-4">
          {user ? (
            <>
              <span>Welcome, {user.username}!</span>
              <Link to="/">Home</Link>
              {/* Add logout button later */}
            </>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <Link to="/register">Register</Link>
            </>
          )}
        </div>
      </nav>
      <main className="container mx-auto p-4">{children}</main>
    </div>
  );
}
