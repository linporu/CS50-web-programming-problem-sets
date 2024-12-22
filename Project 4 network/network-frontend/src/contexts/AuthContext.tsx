import { createContext, useContext, useState, ReactNode } from "react";

// Define user type
interface User {
  username: string;
  email: string;
}

// Define Context type
interface AuthContextType {
  user: User | null;
  setUser: (user: User | null) => void;
  isAuthenticated: boolean;
  logout: () => void;
}

// Create Context
const AuthContext = createContext<AuthContextType | null>(null);

// Context Provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  // Compute isAuthenticated based on user state
  const isAuthenticated = user !== null;

  // Add logout function
  const logout = () => {
    setUser(null);
    // Clear any other auth-related data from localStorage if needed
    localStorage.removeItem("user");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        setUser,
        isAuthenticated,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// Custom Hook to make it easier for other components to use the Context
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
