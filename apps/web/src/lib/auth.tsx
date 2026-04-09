import {
  ClerkProvider,
  SignIn,
  UserButton,
  useAuth,
  useUser,
} from "@clerk/clerk-react";
import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { appConfig, isClerkEnabled } from "@/lib/config";

type AuthState = {
  clerkEnabled: boolean;
  isLoaded: boolean;
  isSignedIn: boolean;
  user: { firstName?: string | null; email?: string | null } | null;
  getToken: () => Promise<string | null>;
  signIn: () => void;
  signOut: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  if (isClerkEnabled) {
    return (
      <ClerkProvider
        publishableKey={appConfig.clerkPublishableKey}
        afterSignOutUrl="/"
        signInFallbackRedirectUrl="/app"
        signUpFallbackRedirectUrl="/app"
      >
        <ClerkBridge>{children}</ClerkBridge>
      </ClerkProvider>
    );
  }

  return <MockAuthProvider>{children}</MockAuthProvider>;
}

function ClerkBridge({ children }: { children: ReactNode }) {
  const clerkAuth = useAuth();
  const { user, isLoaded } = useUser();

  const value = useMemo<AuthState>(
    () => ({
      clerkEnabled: true,
      isLoaded,
      isSignedIn: Boolean(clerkAuth.isSignedIn),
      user: user
        ? {
            firstName: user.firstName,
            email: user.primaryEmailAddress?.emailAddress,
          }
        : null,
      getToken: () => clerkAuth.getToken(),
      signIn: () => {
        window.location.assign("/sign-in");
      },
      signOut: () => clerkAuth.signOut(),
    }),
    [clerkAuth, isLoaded, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function MockAuthProvider({ children }: { children: ReactNode }) {
  const [isSignedIn, setIsSignedIn] = useState(() => localStorage.getItem("and-demo-auth") === "true");

  const value = useMemo<AuthState>(
    () => ({
      clerkEnabled: false,
      isLoaded: true,
      isSignedIn,
      user: isSignedIn
        ? {
            firstName: "Demo",
            email: "demo@and.local",
          }
        : null,
      getToken: async () => (isSignedIn ? "demo-session-token" : null),
      signIn: () => {
        localStorage.setItem("and-demo-auth", "true");
        setIsSignedIn(true);
      },
      signOut: () => {
        localStorage.removeItem("and-demo-auth");
        setIsSignedIn(false);
      },
    }),
    [isSignedIn],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthState() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuthState must be used within AuthProvider.");
  }
  return value;
}

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const auth = useAuthState();
  if (!auth.isLoaded) {
    return null;
  }
  if (!auth.isSignedIn) {
    return <Navigate to="/sign-in" replace />;
  }
  return children;
}

export function AuthSignInCard() {
  const auth = useAuthState();

  if (auth.clerkEnabled) {
    return (
      <div className="overflow-hidden rounded-[1.75rem] border border-border bg-card p-2 shadow-lg shadow-black/5">
        <SignIn signUpUrl={undefined} forceRedirectUrl="/app" fallbackRedirectUrl="/app" />
      </div>
    );
  }

  return null;
}

export function AuthUserButton() {
  const auth = useAuthState();

  if (auth.clerkEnabled) {
    return <UserButton appearance={{ elements: { userButtonAvatarBox: "h-10 w-10" } }} />;
  }

  return null;
}
