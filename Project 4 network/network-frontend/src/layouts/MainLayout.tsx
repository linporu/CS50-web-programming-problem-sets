import { Link } from "react-router-dom";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { logoutUser } from "../services/authService";
import { useAuth } from "../contexts/AuthContext";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, logout } = useAuth();
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const handleLogout = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      await logoutUser(); // Backend logout API
      logout(); // Frontend logout
      navigate("/login");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Logout failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <nav className="bg-gray-100 p-4">
        <h1>Network</h1>
        {error && <div className="text-red-500">{error}</div>}
        <div className="space-x-4">
          {user ? (
            <>
              <span>Welcome, {user.username}!</span>
              <Link to="/">Home</Link>
              <button
                onClick={handleLogout}
                disabled={isLoading}
                className="bg-transparent hover:text-gray-700 disabled:opacity-50"
              >
                {isLoading ? "Logging out..." : "Logout"}
              </button>
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
