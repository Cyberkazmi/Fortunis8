export type Language = "en" | "ur";
export type Focus = "general" | "love" | "work" | "growth";

export const PERSONAS = [
  "Mario",
  "Tarzan",
  "Hercules",
  "Dragon",
  "Ninja",
  "Wizard",
  "Phoenix",
  "Spartan",
  "Viking",
  "Samurai",
  "Pirate",
  "Jedi",
] as const;
export type Persona = typeof PERSONAS[number];

export const SAFETY: Record<Language, string> = {
  en:
    "For entertainment only—this is not a guaranteed prediction, professional advice, or a full astronomical kundli.",
  ur:
    "صرف تفریح کے لیے—یہ یقینی پیش گوئی، پیشہ ورانہ مشورہ، یا مکمل فلکیاتی کنڈلی نہیں ہے۔",
};

const FORTUNES: Record<Language, string[]> = {
  en: [
    "A small change of routine may make today feel brighter.",
    "Notice a useful question before rushing toward an answer.",
    "A kind conversation could open a fresh perspective.",
    "Celebrate progress that is real, even if it is modest.",
  ],
  ur: [
    "معمول میں ایک چھوٹی تبدیلی آج کو روشن محسوس کرا سکتی ہے۔",
    "جواب کی طرف جلدی سے پہلے ایک مفید سوال پر غور کریں۔",
    "ایک مہربان گفتگو نیا نقطۂ نظر کھول سکتی ہے۔",
    "حقیقی پیش رفت کا جشن منائیں، چاہے وہ معمولی ہی ہو۔",
  ],
};
const TAROTS: Record<Language, string[]> = {
  en: [
    "The Lantern: explore one clear next step.",
    "The Bridge: balance two viewpoints.",
    "The Seed: give a small idea patient attention.",
  ],
  ur: [
    "چراغ: اگلے ایک واضح قدم کو تلاش کریں۔",
    "پل: دو نقطۂ نظر میں توازن رکھیں۔",
    "بیج: ایک چھوٹے خیال کو صبر سے وقت دیں۔",
  ],
};
const FOCUS_LABELS: Record<Language, Record<Focus, string>> = {
  en: {
    general: "general",
    love: "relationships",
    work: "work",
    growth: "personal growth",
  },
  ur: { general: "عمومی", love: "رشتے", work: "کام", growth: "ذاتی ترقی" },
};
const STYLES: Record<Persona, string> = {
  Mario: "cheerful and practical",
  Tarzan: "bold and nature-minded",
  Hercules: "steady and encouraging",
  Dragon: "calm and watchful",
  Ninja: "quiet and focused",
  Wizard: "curious and thoughtful",
  Phoenix: "hopeful and resilient",
  Spartan: "disciplined and direct",
  Viking: "adventurous and loyal",
  Samurai: "patient and honorable",
  Pirate: "playful and resourceful",
  Jedi: "balanced and reflective",
};
const STYLES_UR: Record<Persona, string> = {
  Mario: "خوش مزاج اور عملی",
  Tarzan: "دلیر اور فطرت دوست",
  Hercules: "مستقل مزاج اور حوصلہ افزا",
  Dragon: "پرسکون اور چوکس",
  Ninja: "خاموش اور یکسو",
  Wizard: "متجسس اور غوروفکر کرنے والا",
  Phoenix: "پرامید اور ثابت قدم",
  Spartan: "منظم اور صاف گو",
  Viking: "مہم جو اور وفادار",
  Samurai: "صابر اور بااصول",
  Pirate: "شوخ اور وسائل والا",
  Jedi: "متوازن اور عکاس",
};

async function indexFor(seed: string, size: number): Promise<number> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(seed),
  );
  return Number(new DataView(digest).getBigUint64(0, false) % BigInt(size));
}

export async function fortune(
  language: Language,
  seed: string,
): Promise<string> {
  return `${
    FORTUNES[language][await indexFor(seed, FORTUNES[language].length)]
  } ${SAFETY[language]}`;
}

export async function tarot(language: Language, seed: string): Promise<string> {
  return `${TAROTS[language][await indexFor(seed, TAROTS[language].length)]} ${
    SAFETY[language]
  }`;
}

export function palmReading(
  focus: Focus,
  language: Language,
  premium = false,
): string {
  const label = FOCUS_LABELS[language][focus];
  const text = language === "en"
    ? premium
      ? `A longer palm-themed reflection for ${label}: compare your priorities, try one gentle experiment, and review how it feels. No image processing is performed.`
      : `A playful palm-themed reflection for ${label}: notice patterns, choices, and what you can influence.`
    : premium
    ? `${label} کے لیے ہتھیلی سے متاثر تفصیلی غور: ترجیحات کا موازنہ کریں، ایک نرم تجربہ کریں، اور احساس کا جائزہ لیں۔ تصویر پر کارروائی نہیں کی جاتی۔`
    : `${label} کے لیے ہتھیلی سے متاثر ایک تفریحی غور: نمونوں، انتخابوں اور اپنے اختیار والی چیزوں کو دیکھیں۔`;
  return `${text} ${SAFETY[language]}`;
}

export function personaStyle(persona: string, language: Language): string {
  if (!PERSONAS.includes(persona as Persona)) {
    return language === "ur" ? "متوازن" : "balanced";
  }
  const key = persona as Persona;
  return language === "ur" ? STYLES_UR[key] : STYLES[key];
}

export function withPersona(
  text: string,
  persona: string,
  language: Language,
): string {
  return language === "ur"
    ? `${text}\n\nمنتخب رہنما: ${persona} — ${
      personaStyle(persona, language)
    } انداز۔`
    : `${text}\n\nYour guide, ${persona}, brings a ${
      personaStyle(persona, language)
    } lens.`;
}

export function sunSign(dateText: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateText);
  if (!match) throw new Error("invalid_date");
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const parsed = new Date(Date.UTC(year, month - 1, day));
  if (
    parsed.getUTCFullYear() !== year || parsed.getUTCMonth() !== month - 1 ||
    parsed.getUTCDate() !== day
  ) {
    throw new Error("invalid_date");
  }
  const monthDay = month * 100 + day;
  const boundaries: Array<[number, string]> = [
    [120, "Aquarius"],
    [219, "Pisces"],
    [321, "Aries"],
    [420, "Taurus"],
    [521, "Gemini"],
    [621, "Cancer"],
    [723, "Leo"],
    [823, "Virgo"],
    [923, "Libra"],
    [1023, "Scorpio"],
    [1122, "Sagittarius"],
    [1222, "Capricorn"],
  ];
  for (let i = boundaries.length - 1; i >= 0; i--) {
    if (monthDay >= boundaries[i][0]) return boundaries[i][1];
  }
  return "Capricorn";
}

export async function horoscopeReading(
  dateText: string,
  timeText: string,
  location: string,
  language: Language,
): Promise<{ content: string; sign: string }> {
  const cleanLocation = location.trim().replace(/\s+/g, " ");
  if (
    !cleanLocation || cleanLocation.length > 120 ||
    !/^([01]\d|2[0-3]):[0-5]\d$/.test(timeText)
  ) {
    throw new Error("invalid_horoscope");
  }
  const sign = sunSign(dateText);
  const seed = `${dateText}|${timeText}|${cleanLocation}`;
  const themes = language === "en"
    ? ["curiosity", "patience", "clear communication", "steady creativity"]
    : ["تجسس", "صبر", "واضح ابلاغ", "مستقل تخلیق"];
  const theme = themes[await indexFor(seed, themes.length)];
  const message = language === "ur"
    ? `آپ کا تفریحی سورج نشان ${sign} ہے؛ آج کا ذاتی موضوع ${theme} ہے۔ وقت اور مقام صرف اس متن کو متعین کرنے کے لیے استعمال ہوئے ہیں۔`
    : `Your entertainment sun sign is ${sign}; today’s personalized theme is ${theme}. Time and location only shape this text.`;
  return { content: `${message} ${SAFETY[language]}`, sign };
}

export function focusLabel(focus: Focus, language: Language): string {
  return FOCUS_LABELS[language][focus];
}

export function parseFocus(value: string): Focus | null {
  return value === "general" || value === "love" || value === "work" ||
      value === "growth"
    ? value
    : null;
}

export const GAME = {
  en: {
    easy: {
      question: "What is 2 + 2?",
      answer: "4",
      reward: 10,
      options: ["3", "4", "5"],
    },
    hard: {
      question: "What is the square root of 144?",
      answer: "12",
      reward: 50,
      options: ["10", "12", "14"],
    },
  },
  ur: {
    easy: {
      question: "2 + 2 کتنے ہوتے ہیں؟",
      answer: "4",
      reward: 10,
      options: ["3", "4", "5"],
    },
    hard: {
      question: "144 کا مربع جذر کیا ہے؟",
      answer: "12",
      reward: 50,
      options: ["10", "12", "14"],
    },
  },
} as const;
