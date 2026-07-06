export const REFLECTION_PROMPTS = [
  "What made you smile today?",
  "What's currently on your mind?",
  "What challenged you today?",
  "What are you grateful for?",
  "What emotion best describes your day?",
  "What is something you're proud of today?",
];

export const MOODS = [
  { emoji: "😊", label: "Happy" },
  { emoji: "😌", label: "Calm" },
  { emoji: "😐", label: "Neutral" },
  { emoji: "😔", label: "Sad" },
  { emoji: "😰", label: "Anxious" },
  { emoji: "😡", label: "Frustrated" },
] as const;

export const WELLNESS_REMINDERS = [
  { icon: "🌿", text: "Drink some water" },
  { icon: "🌸", text: "Be kind to yourself" },
  { icon: "🌞", text: "Take a short walk" },
  { icon: "💙", text: "Progress is not always visible" },
  { icon: "🌱", text: "Healing takes time" },
];

export const MOTIVATIONAL_QUOTES = [
  { text: "Writing is a conversation with your heart.", author: "Unknown" },
  { text: "In the pages of your journal, you meet yourself again and again.", author: "Unknown" },
  { text: "Your story matters. Every word you write is an act of courage.", author: "Unknown" },
  { text: "The quieter you become, the more you can hear.", author: "Ram Dass" },
  { text: "Feelings are much like waves — we can't stop them from coming, but we can choose which ones to surf.", author: "Jonatan Mårtensson" },
  { text: "Almost everything will work again if you unplug it for a few minutes — including you.", author: "Anne Lamott" },
];

export const WRITING_REMINDERS = [
  "There is no perfect way to journal.",
  "Write honestly. Every thought matters.",
  "Let your words flow without judgment.",
  "This moment is yours — take all the time you need.",
];

export function pickRandom<T>(items: readonly T[]): T {
  return items[Math.floor(Math.random() * items.length)]!;
}
