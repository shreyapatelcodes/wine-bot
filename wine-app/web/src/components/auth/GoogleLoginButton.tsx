/**
 * Google OAuth login button component
 */

import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../../context/AuthContext';

interface GoogleLoginButtonProps {
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

export function GoogleLoginButton({ onSuccess, onError }: GoogleLoginButtonProps) {
  const { login, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center w-full px-4 py-3 bg-gray-100 text-gray-500 border border-gray-300 rounded-lg">
        <span className="font-medium">Signing in...</span>
      </div>
    );
  }

  return (
    <GoogleLogin
      onSuccess={async (credentialResponse) => {
        try {
          if (!credentialResponse.credential) {
            throw new Error('No credential received from Google');
          }
          await login(credentialResponse.credential);
          onSuccess?.();
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Login failed';
          onError?.(message);
        }
      }}
      onError={() => {
        onError?.('Google login failed');
      }}
      theme="outline"
      size="large"
      width="100%"
    />
  );
}
