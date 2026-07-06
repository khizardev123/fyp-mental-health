import { LoginForm } from "@/components/login/LoginForm";
import { AuthHeader } from "@/components/ui/AuthHeader";
import { AuthPanel } from "@/components/ui/AuthPanel";

export default function LoginPage() {
  return (
    <div className="page-shell">
      <AuthHeader ctaHref="/signup" ctaLabel="Create account" />

      <main className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-6xl flex-col gap-12 px-6 py-12 lg:flex-row lg:items-start lg:justify-between lg:gap-16 lg:py-16">
        <div className="fade-in flex-1 lg:max-w-md">
          <p className="mb-3 text-sm text-foreground-secondary">
            Welcome back. Sign in to continue your SereneMind journey.
          </p>
          <h1 className="section-title mb-8">Sign in</h1>
          <LoginForm />
        </div>

        <AuthPanel variant="login" accent="blue" />
      </main>
    </div>
  );
}
