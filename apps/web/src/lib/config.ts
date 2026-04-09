export const appConfig = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL?.trim() ?? "",
  clerkPublishableKey: import.meta.env.VITE_CLERK_PUBLISHABLE_KEY?.trim() ?? "",
};

export const isDemoMode = !appConfig.apiBaseUrl;
export const isClerkEnabled = Boolean(appConfig.clerkPublishableKey);
