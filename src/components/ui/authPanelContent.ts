export const AUTH_QUOTES = [
  "Every emotion deserves to be understood.",
  "Healing begins with honesty.",
  "You don't have to carry every thought alone.",
  "Small reflections create meaningful growth.",
];

export const AUTH_FEATURES = [
  { id: "journal", label: "Private journaling" },
  { id: "insights", label: "Emotion insights" },
  { id: "companion", label: "Supportive AI companion" },
] as const;

export const AUTH_VARIANTS = {
  login: {
    heading: "Welcome to SereneMind",
    message: "Reflect, journal, and feel gently supported.",
    calm: "Take a breath — you're in the right place.",
  },
  signup: {
    heading: "Your safe space begins here",
    message: "Nurture your wellbeing with caring AI support.",
    calm: "Every journey begins with a single moment of care.",
  },
} as const;

export function pickRandom<T>(items: readonly T[]): T {
  return items[Math.floor(Math.random() * items.length)]!;
}
