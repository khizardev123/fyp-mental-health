"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { AppHeader } from "@/components/ui/AppHeader";
import { LoadingScreen } from "@/components/ui/LoadingScreen";

type ProfileUser = {
  id: string;
  name: string;
  email: string;
  preferences: string;
  emotionalGoals: string;
  bio: string;
};

export default function ProfilePage() {
  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [preferences, setPreferences] = useState("");
  const [emotionalGoals, setEmotionalGoals] = useState("");
  const [bio, setBio] = useState("");
  const [saveState, setSaveState] = useState<"idle" | "saving" | "success" | "error">("idle");
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const fetchProfile = useCallback(async () => {
    setLoadState("loading");
    setLoadError(null);
    try {
      const res = await fetch("/api/profile", { credentials: "same-origin" });
      const data = (await res.json()) as { user?: ProfileUser; error?: string };
      if (!res.ok || !data.user) {
        setLoadState("error");
        setLoadError(data.error ?? "Could not load profile.");
        return;
      }
      const u = data.user;
      setName(u.name);
      setEmail(u.email);
      setPreferences(u.preferences);
      setEmotionalGoals(u.emotionalGoals);
      setBio(u.bio);
      setLoadState("ready");
    } catch {
      setLoadState("error");
      setLoadError("Network error. Please try again.");
    }
  }, []);

  useEffect(() => { fetchProfile(); }, [fetchProfile]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaveMessage(null);
    if (!name.trim()) {
      setSaveState("error");
      setSaveMessage("Name is required.");
      return;
    }
    setSaveState("saving");
    try {
      const res = await fetch("/api/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({
          name: name.trim(),
          preferences: preferences.trim(),
          emotionalGoals: emotionalGoals.trim(),
          bio: bio.trim(),
        }),
      });

      const data = (await res.json()) as {
        error?: string;
        message?: string;
        fieldErrors?: Record<string, string[] | undefined>;
        formErrors?: string[];
        user?: ProfileUser;
      };

      if (!res.ok) {
        setSaveState("error");
        const parts: string[] = [];
        if (data.fieldErrors) {
          Object.values(data.fieldErrors).forEach((msgs) => {
            msgs?.forEach((m) => parts.push(m));
          });
        }
        if (data.formErrors?.length) parts.push(...data.formErrors);
        setSaveMessage(
          parts.length > 0 ? parts.join(" ") : data.error ?? "Update failed.",
        );
        return;
      }

      setSaveState("success");
      setSaveMessage(data.message ?? "Profile updated.");
      if (data.user) {
        setName(data.user.name);
        setPreferences(data.user.preferences);
        setEmotionalGoals(data.user.emotionalGoals);
        setBio(data.user.bio);
      }
    } catch {
      setSaveState("error");
      setSaveMessage("Network error. Please try again.");
    }
  }

  if (loadState === "loading") {
    return <LoadingScreen message="Loading profile…" />;
  }

  if (loadState === "error") {
    return (
      <div className="page-shell flex flex-col items-center justify-center px-6 text-center">
        <p className="text-foreground-secondary">{loadError}</p>
        <Link href="/login" className="btn-primary mt-6">
          Sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="page-shell">
      <AppHeader
        maxWidth="3xl"
        nav={[
          { href: "/dashboard", label: "Dashboard" },
          { href: "/chat", label: "Chat" },
          { href: "/journal", label: "Journal" },
        ]}
      />

      <main className="page-main-narrow fade-in">
        <div className="mb-10">
          <h1 className="section-title">Your profile</h1>
          <p className="section-subtitle">
            Tell SereneMind about your preferences and goals so responses can
            feel more personal. Passwords are never shown here.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="card-padded space-y-8">
          {saveMessage && (
            <div
              role="alert"
              className={
                saveState === "success" ? "alert-success" : "alert-error"
              }
            >
              {saveMessage}
            </div>
          )}

          <div className="grid gap-6 sm:grid-cols-2">
            <div>
              <label htmlFor="profile-name" className="label-muted">
                Name
              </label>
              <input
                id="profile-name"
                name="name"
                type="text"
                autoComplete="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={120}
                className="input-field"
              />
              <p className="mt-1.5 text-right text-xs text-foreground-secondary">
                {name.length}/120
              </p>
            </div>
            <div>
              <label className="label-muted">Email</label>
              <input
                type="email"
                value={email}
                readOnly
                className="input-readonly"
              />
            </div>
          </div>

          <div>
            <label htmlFor="preferences" className="label-text">
              Preferences
            </label>
            <p className="mb-3 text-xs text-foreground-secondary">
              Topics, tone, or habits you want the experience to respect (max
              500 characters).
            </p>
            <textarea
              id="preferences"
              name="preferences"
              rows={3}
              value={preferences}
              onChange={(e) => setPreferences(e.target.value)}
              maxLength={500}
              className="textarea-field"
              placeholder="e.g. I prefer gentle, encouraging language…"
            />
            <p className="mt-1.5 text-right text-xs text-foreground-secondary">
              {preferences.length}/500
            </p>
          </div>

          <div>
            <label htmlFor="emotionalGoals" className="label-text">
              Emotional goals
            </label>
            <p className="mb-3 text-xs text-foreground-secondary">
              What you are working toward emotionally (max 1000 characters).
            </p>
            <textarea
              id="emotionalGoals"
              name="emotionalGoals"
              rows={4}
              value={emotionalGoals}
              onChange={(e) => setEmotionalGoals(e.target.value)}
              maxLength={1000}
              className="textarea-field"
              placeholder="e.g. Building more self-compassion and managing stress…"
            />
            <p className="mt-1.5 text-right text-xs text-foreground-secondary">
              {emotionalGoals.length}/1000
            </p>
          </div>

          <div>
            <label htmlFor="bio" className="label-text">
              Bio{" "}
              <span className="font-normal text-foreground-secondary">
                (optional)
              </span>
            </label>
            <textarea
              id="bio"
              name="bio"
              rows={4}
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              maxLength={2000}
              className="textarea-field"
              placeholder="A little about you, if you'd like to share…"
            />
            <p className="mt-1.5 text-right text-xs text-foreground-secondary">
              {bio.length}/2000
            </p>
          </div>

          <button
            type="submit"
            disabled={saveState === "saving"}
            className="btn-primary"
          >
            {saveState === "saving" ? "Saving…" : "Save profile"}
          </button>
        </form>
      </main>
    </div>
  );
}
