// Import necessary hooks and types from React and our auth service
import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { checkAuthStatus } from "../services/authService";

// Define the User interface that matches our API response structure
// This represents the authenticated user's data
interface User {
  id: number;
  username: string;
  email: string;
  following_count: number;
  follower_count: number;
}

// Define the shape of our Authentication Context
// This interface specifies all values and functions that will be available through the context
interface AuthContextType {
  user: User | null;                    // Current user data or null if not authenticated
  setUser: (user: User | null) => void; // Function to update user data
  isAuthenticated: boolean;             // Quick check if user is logged in
  clearAuth: () => void;                // Function to log out user
  loading?: boolean;                    // Loading state during auth checks
  _isDefault?: boolean;                 // Internal flag to check if using default context
}

// Create default values for the context
// This is used when a component tries to use the context outside of a provider
const defaultContextValue: AuthContextType = {
  user: null,
  setUser: () => {},
  isAuthenticated: false,
  clearAuth: () => {},
};

// Create the context with default values
// The _isDefault flag helps us detect when context is being used outside provider
const AuthContext = createContext<AuthContextType>({
  ...defaultContextValue,
  _isDefault: true,
});

// AuthProvider component that wraps the app and provides authentication state
// This component manages the global auth state and provides it to all children
export function AuthProvider({ children }: { children: ReactNode }) {
  // State to store user data and loading status
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Effect hook to verify authentication status when component mounts
  useEffect(() => {
    const verifyAuth = async () => {
      try {
        // Check with backend if user is authenticated
        const response = await checkAuthStatus();
        setUser(response.user);
      } catch (error) {
        // If verification fails, clear user data
        console.error("Auth verification failed:", error);
        setUser(null);
      } finally {
        // Always set loading to false when done
        setLoading(false);
      }
    };

    verifyAuth();
  }, []);

  // Derived state to check if user is authenticated
  const isAuthenticated = user !== null;

  // Function to clear authentication data (logout)
  const clearAuth = () => {
    setUser(null);
    localStorage.removeItem("user");
  };

  // Provide the authentication context to children components
  // Shows loading state while verifying authentication
  return (
    <AuthContext.Provider
      value={{
        user,
        setUser,
        isAuthenticated,
        clearAuth,
        _isDefault: false, // Indicate this is a real provider, not default context
      }}
    >
      {loading ? <div>Loading...</div> : children}
    </AuthContext.Provider>
  );
}

// Custom hook to use the auth context in components
// This provides a cleaner API and better error handling for context usage
export function useAuth() {
  const context = useContext(AuthContext);
  // Throw error if hook is used outside of AuthProvider
  if (!context || context._isDefault) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
