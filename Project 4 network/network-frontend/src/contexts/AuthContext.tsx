import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { checkAuthStatus } from "../services/authService";

// Update User interface to match LoginResponse
interface User {
  id: number;
  username: string;
  email: string;
  following_count: number;
  follower_count: number;
}

// Define Context type
interface AuthContextType {
  user: User | null;
  setUser: (user: User | null) => void;
  isAuthenticated: boolean;
  logout: () => void;
  loading?: boolean;
  _isDefault?: boolean;
}

// Add a flag to identify default context
const defaultContextValue: AuthContextType = {
  user: null,
  setUser: () => {},
  isAuthenticated: false,
  logout: () => {},
};

const AuthContext = createContext<AuthContextType>({
  ...defaultContextValue,
  _isDefault: true,
});

// Context Provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verifyAuth = async () => {
      try {
        const response = await checkAuthStatus();
        setUser(response.user);
      } catch (error) {
        console.error("Auth verification failed:", error);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    verifyAuth();
  }, []);

  const isAuthenticated = user !== null;
  const logout = () => {
    setUser(null);
    localStorage.removeItem("user");
  };

  // Important: Provide Context even during loading
  return (
    <AuthContext.Provider
      value={{
        user,
        setUser,
        isAuthenticated,
        logout,
        _isDefault: false, // Value provided by Provider is not default
      }}
    >
      {loading ? <div>Loading...</div> : children}
    </AuthContext.Provider>
  );
}

// Custom Hook to make it easier for other components to use the Context
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context || context._isDefault) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
