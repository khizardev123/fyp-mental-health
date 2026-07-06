import { SignupForm } from "@/components/signup/SignupForm";
import { AuthHeader } from "@/components/ui/AuthHeader";
import { AuthPanel } from "@/components/ui/AuthPanel";

export default function SignupPage() {
  return (
    <div className="page-shell">
      <AuthHeader ctaHref="/login" ctaLabel="Sign in" />

      <main className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-6xl flex-col gap-12 px-6 py-12 lg:flex-row lg:items-start lg:justify-between lg:gap-16 lg:py-16">
        <div className="fade-in flex-1 lg:max-w-md">
          <p className="mb-3 text-sm text-foreground-secondary">
            Create your SereneMind account to access a safe, supportive space.
          </p>
          <h1 className="section-title mb-8">Sign up</h1>
          <SignupForm />
        </div>

        <AuthPanel variant="signup" accent="lavender" />
      </main>
    </div>
  );
}
