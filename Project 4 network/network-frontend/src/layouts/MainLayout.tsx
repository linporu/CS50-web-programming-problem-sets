import { Link } from "react-router-dom";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div>
      <nav className="bg-gray-100 p-4">
        <h1>Network</h1>
        <div className="space-x-4">
          <Link to="/login">Login</Link>
          <Link to="/register">Register</Link>
        </div>
      </nav>
      <main className="container mx-auto p-4">{children}</main>
    </div>
  );
}
