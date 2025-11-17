"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
  useRef,
} from "react";
import { USER_KEY, USER_TOKEN } from "@/lib/constants";

// import lyzr from "../../lyzr-agent-local";

// The token data returned by the SDK.getKeys() call.
interface TokenData {
  user_id: string;
  api_key: string;
}

// Example shape from SDK.getKeysUser() if it includes permissions now.
interface SdkUserData {
  data: {
    org_id: string;
    available_credits: string;
    user: {
      user_id: string;
      email: string;
      organization_ids: string[];
      current_org_id: string;
    };
  };
}

interface UserType {
  email: string;
  user_id: string;
  organization_ids: string[];
  current_org_id: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  userId: string | null;
  token: string | null;
  user: UserType | null;
  checkAuth: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  isLoading: true,
  userId: null,
  token: null,
  user: null,
  checkAuth: async () => {},
  logout: async () => {},
});

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isInitializing, setIsInitializing] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [userId, setUserId] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserType | null>(null);
  const isInitializedRef = useRef(false);

  // A helper to re-check authentication when called.
  const checkAuth = async () => {
    if (isInitializing) return; // Prevent multiple simultaneous checks

    try {
      setIsInitializing(true);
      const { default: lyzr } = await import("../../lyzr-agent-local");

      // 1. Get basic token data: API key + user_id
      const tokenData = (await lyzr.getKeys()) as unknown as TokenData[];

      if (tokenData && tokenData[0]) {
        // 2. Get additional user details + bearer token
        const sdkUserData = (await lyzr.getKeysUser()) as SdkUserData;
        console.log("SDK user data:", tokenData[0]);

        // Save localStorage items
        localStorage.setItem(USER_KEY, tokenData[0].api_key);
        const params = new URLSearchParams(window.location.search);
        const urlToken = params.get("token");
        if (urlToken) {
          localStorage.setItem(USER_TOKEN, urlToken);
        }
        localStorage.setItem("user_id", tokenData[0].user_id);

        // Build a user object
        const userObj: UserType = {
          email: sdkUserData.data.user.email,
          user_id: sdkUserData.data.user.user_id,
          organization_ids: sdkUserData.data.user.organization_ids,
          current_org_id: sdkUserData.data.user.current_org_id,
        };

        localStorage.setItem("USER_DATA", JSON.stringify(userObj));

        // Only update state if not already authenticated or if token changed
        if (!isAuthenticated || urlToken !== token) {
          setIsAuthenticated(true);
          setUserId(tokenData[0].user_id);
          setToken(urlToken || sdkUserData.data.org_id);
          setUser(userObj);
        }
      } else {
        handleAuthFailure();
      }
    } catch (err: any) {
      console.error("Auth check failed:", err);

      // Check if it's a 401 error (token expired)
      if (err?.message?.includes("401") || err?.message?.includes("Unauthorized")) {
        console.warn("Authentication token expired. Clearing local storage and forcing re-login.");
        // Clear all auth data
        handleAuthFailure();
        // Also clear any Lyzr SDK stored data
        try {
          const { default: lyzr } = await import("../../lyzr-agent-local");
          await lyzr.logout();
        } catch (logoutErr) {
          console.error("Error during forced logout:", logoutErr);
        }
      } else {
        handleAuthFailure();
      }
    } finally {
      setIsInitializing(false);
      setIsLoading(false);
    }
  };

  // Called if authentication fails or if user logs out
  const handleAuthFailure = () => {
    setIsAuthenticated(false);
    setUserId(null);
    setToken(null);
    setUser(null);

    // Clear all localStorage items related to auth
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(USER_TOKEN);
    localStorage.removeItem("user_id");
    localStorage.removeItem("USER_DATA");

    // Clear any Lyzr SDK specific storage (may use different keys)
    // This is more aggressive but prevents 401 loops
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && (key.includes("lyzr") || key.includes("auth") || key.includes("token"))) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach(key => localStorage.removeItem(key));

    // Also clear sessionStorage
    sessionStorage.clear();
  };

  // Add a logout function that calls lyzr.logout + clears local data
  const logout = async () => {
    try {
      const { default: lyzr } = await import("../../lyzr-agent-local");
      await lyzr.logout(); // log out from the SDK
      handleAuthFailure();
    } catch (err) {
      console.error("Failed to log out from lyzr:", err);
    }

    // Clear local data
    handleAuthFailure();

    // Remove any query parameters from URL after logout
    const currentUrl = new URL(window.location.href);
    const cleanUrl = `${currentUrl.origin}${currentUrl.pathname}`;
    window.history.replaceState({}, document.title, cleanUrl);
  };

  // Check for token in URL parameter first, then load stored auth info
  useEffect(() => {
    // Check URL first for token parameter
    const urlParams = new URLSearchParams(window.location.search);
    const urlToken = urlParams.get("token");

    if (urlToken) {
      // Token found in URL, store it in localStorage
      localStorage.setItem(USER_TOKEN, urlToken);
      setToken(urlToken);
      setIsAuthenticated(true);
      setIsLoading(false);

      return;
    }

    // No token in URL, attempt to load stored auth info
    const storedKey = localStorage.getItem(USER_KEY);
    const storedBearerToken = localStorage.getItem(USER_TOKEN);
    const storedUserData = localStorage.getItem("USER_DATA");

    if (storedKey && storedBearerToken && storedUserData && !isAuthenticated) {
      try {
        const parsedUser = JSON.parse(storedUserData) as UserType;
        setUser(parsedUser);
        setIsAuthenticated(true);
        setToken(storedBearerToken);
        setIsLoading(false);
      } catch (error) {
        console.error("Error parsing stored user data", error);
        setIsLoading(false);
      }
    } else {
      setIsLoading(false);
    }
  }, []);

  // Initialize the SDK and set up an auth state listener.
  useEffect(() => {
    let unsubscribe: (() => void) | undefined;

    const init = async () => {
      if (isInitializedRef.current) return; // Use persistent ref

      try {
        const { default: lyzr } = await import("../../lyzr-agent-local");

        await lyzr.init("pk_c14a2728e715d9ea67bf");
        isInitializedRef.current = true; // Mark as initialized

        unsubscribe = lyzr.onAuthStateChange((sdkAuthState) => {
          if (sdkAuthState && !isAuthenticated) {
            checkAuth();
          } else if (!sdkAuthState) {
            handleAuthFailure();
          }
        });

        // Only check auth if not already authenticated
        if (!isAuthenticated) {
          await checkAuth();
        }
      } catch (err) {
        console.error("Initialization failed:", err);
        setIsLoading(false);
      }
    };

    init();
    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, []);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        userId,
        token,
        user,
        checkAuth,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
