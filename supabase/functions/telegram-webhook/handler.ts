import {
  type Focus,
  fortune,
  GAME,
  horoscopeReading,
  type Language,
  palmReading,
  parseFocus,
  type Persona,
  PERSONAS,
  tarot,
  withPersona,
} from "./domain.ts";
import {
  type Fetcher,
  Fortunis8Store,
  type JsonRecord,
  requiredSecrets,
} from "./store.ts";

export interface HandlerDependencies {
  env: (name: string) => string | undefined;
  fetcher?: Fetcher;
  now?: () => Date;
}

interface TelegramUser {
  id: number;
}
interface TelegramChat {
  id: number;
  type: string;
}
interface TelegramMessage {
  message_id: number;
  chat: TelegramChat;
  from?: TelegramUser;
  text?: string;
  photo?: unknown[];
  successful_payment?: {
    invoice_payload: string;
    telegram_payment_charge_id: string;
    total_amount: number;
    currency: string;
  };
}
interface TelegramCallback {
  id: string;
  from: TelegramUser;
  data?: string;
  message?: TelegramMessage;
}
interface TelegramPreCheckout {
  id: string;
  from: TelegramUser;
  invoice_payload: string;
  total_amount: number;
  currency: string;
}
interface TelegramUpdate {
  update_id: number;
  message?: TelegramMessage;
  callback_query?: TelegramCallback;
  pre_checkout_query?: TelegramPreCheckout;
}

type Button = { text: string; callback_data: string };
type Keyboard = { inline_keyboard: Button[][] };

const COPY: Record<Language, Record<string, string>> = {
  en: {
    welcome:
      "Welcome to Fortunis8. Choose English or Urdu, then open the menu. Readings are for entertainment only.",
    language_saved: "Language saved: English.",
    menu: "Fortunis8 menu — readings and games are for entertainment only.",
    private_only: "Please use Fortunis8 in a private Telegram chat.",
    unavailable:
      "Fortunis8 is temporarily unavailable. Please try again later.",
    help:
      "Commands: /start, /menu, /fortune, /tarot, /horoscope, /palm, /games, /daily, /profile, /leaderboard, /personas, /charity, /last. Readings are for entertainment only.",
    horoscope_prompt:
      "For privacy, send the complete request in one message: /horoscope YYYY-MM-DD HH:MM, City (example: /horoscope 1995-08-20 09:30, Lahore). Date, time, and location are not saved.",
    horoscope_invalid:
      "That format was not recognized. Use /horoscope YYYY-MM-DD HH:MM, City. These details are used once and are not saved.",
    horoscope_future:
      "Please use a valid past birth date. The details are not saved.",
    focus:
      "Choose a focus. This palm-themed text reflection does not analyze hand photos.",
    basic_title: "Basic palm-themed reflection",
    premium_title: "Detailed palm-themed reflection",
    premium_price:
      "Choose a focus for one detailed reading ({price} Telegram Stars). Diamonds are not sold.",
    credits_available:
      "You have {credits} premium reading credit(s). Choose a focus to use one.",
    payment_credit:
      "Payment verified. Your detailed reading is below. Remaining credit(s): {credits}.",
    premium_update_duplicate:
      "This Telegram request was already processed. Use /last to view your latest saved reading.",
    payment_pending:
      "Payment verified. Your premium reading credit is ready. Open /palm to use it.",
    payment_duplicate:
      "This Telegram Stars payment was already processed. Use /last to view your latest saved reading.",
    payment_invalid:
      "We could not verify this payment. Do not pay again; please contact the bot owner.",
    payment_unavailable:
      "Payment verification is temporarily unavailable. Please try again later.",
    precheckout_failed:
      "This Stars invoice is invalid or expired. No payment was taken.",
    invoice_unavailable:
      "A Stars invoice could not be created. You were not charged.",
    game_choose:
      "Choose a no-cost skill challenge. Hard mode offers more diamonds for a correct answer; diamonds have no cash value.",
    game_expired: "This challenge expired. Start a new one from /games.",
    game_used: "That challenge was already submitted.",
    game_wrong: "Not quite. No diamonds were deducted; try another challenge.",
    game_correct: "Correct. +{reward} diamonds. Balance: {balance}.",
    daily_done: "Today's daily reward was already claimed.",
    daily_claim:
      "Daily reward: +{reward} diamonds. Streak: {streak}. Balance: {balance}.",
    profile:
      "Diamonds: {diamonds}\nLevel: {level}\nDaily streak: {streak}\nPremium reading credits: {credits}\nPersona: {persona}",
    no_reading: "No saved reading yet. Choose a reading from /menu.",
    leaderboard:
      "Anonymous leaderboard (diamonds only):\n{rows}\n\nYour place: {rank}",
    leaderboard_empty: "The leaderboard is empty so far.",
    personas:
      "Choose a persona. These are neutral style labels, not character impersonations.",
    persona_saved: "Persona saved: {persona}.",
    charity:
      "Optional quest: share a kind word or support a cause you trust—only if you want to. No donation or proof is requested.",
    quest_claimed: "Quest complete: +{reward} diamonds. Balance: {balance}.",
    quest_duplicate: "You already completed that optional quest today.",
    palm_photo:
      "This version does not analyze or save hand photos. Use /palm for a focus-based text reflection.",
    premium_unavailable:
      "A premium credit could not be used just now. Your account balance is unchanged if the request did not complete; try /palm again later.",
  },
  ur: {
    welcome:
      "Fortunis8 میں خوش آمدید۔ اردو یا English منتخب کریں، پھر مینو کھولیں۔ تمام مطالعے صرف تفریح کے لیے ہیں۔",
    language_saved: "زبان اردو محفوظ کر دی گئی ہے۔",
    menu: "Fortunis8 مینو — مطالعے اور کھیل صرف تفریح کے لیے ہیں۔",
    private_only: "براہِ کرم Fortunis8 کو نجی Telegram چیٹ میں استعمال کریں۔",
    unavailable: "Fortunis8 عارضی طور پر دستیاب نہیں۔ بعد میں کوشش کریں۔",
    help:
      "کمانڈز: /start، /menu، /fortune، /tarot، /horoscope، /palm، /games، /daily، /profile، /leaderboard، /personas، /charity، /last۔ تمام مطالعے صرف تفریح کے لیے ہیں۔",
    horoscope_prompt:
      "رازداری کے لیے مکمل درخواست ایک ہی پیغام میں بھیجیں: /horoscope YYYY-MM-DD HH:MM, City (مثال: /horoscope 1995-08-20 09:30, Lahore)۔ تاریخ، وقت اور مقام محفوظ نہیں ہوتے۔",
    horoscope_invalid:
      "فارمیٹ درست نہیں۔ /horoscope YYYY-MM-DD HH:MM, City استعمال کریں۔ معلومات صرف ایک بار استعمال ہوں گی اور محفوظ نہیں ہوں گی۔",
    horoscope_future:
      "براہِ کرم پیدائش کی درست ماضی کی تاریخ استعمال کریں۔ معلومات محفوظ نہیں ہوں گی۔",
    focus:
      "ایک موضوع منتخب کریں۔ یہ ہتھیلی سے متاثر تحریری غور ہے؛ ہاتھ کی تصویر کا تجزیہ نہیں ہوتا۔",
    basic_title: "ہتھیلی سے متاثر بنیادی تفریحی غور",
    premium_title: "ہتھیلی سے متاثر تفصیلی غور",
    premium_price:
      "ایک تفصیلی مطالعے کے لیے موضوع منتخب کریں ({price} Telegram Stars)۔ ڈائمنڈز فروخت نہیں ہوتے۔",
    credits_available:
      "آپ کے پاس {credits} پریمیم مطالعے کا کریڈٹ ہے۔ استعمال کے لیے موضوع منتخب کریں۔",
    payment_credit:
      "ادائیگی کی تصدیق ہو گئی۔ آپ کا تفصیلی مطالعہ نیچے ہے۔ باقی کریڈٹ: {credits}۔",
    premium_update_duplicate:
      "یہ Telegram درخواست پہلے ہی پراسیس ہو چکی ہے۔ تازہ ترین محفوظ مطالعے کے لیے /last بھیجیں۔",
    payment_pending:
      "ادائیگی کی تصدیق ہو گئی۔ پریمیم کریڈٹ تیار ہے؛ استعمال کے لیے /palm کھولیں۔",
    payment_duplicate:
      "یہ Telegram Stars ادائیگی پہلے ہی پراسیس ہو چکی ہے۔ تازہ ترین محفوظ مطالعے کے لیے /last بھیجیں۔",
    payment_invalid:
      "ادائیگی کی تصدیق نہیں ہو سکی۔ دوبارہ ادائیگی نہ کریں؛ بوٹ کے مالک سے رابطہ کریں۔",
    payment_unavailable:
      "ادائیگی کی تصدیق عارضی طور پر دستیاب نہیں۔ بعد میں کوشش کریں۔",
    precheckout_failed:
      "یہ Stars invoice غلط یا ختم شدہ ہے۔ ادائیگی نہیں لی گئی۔",
    invoice_unavailable:
      "ابھی Stars invoice نہیں بن سکا۔ آپ سے ادائیگی نہیں لی گئی۔",
    game_choose:
      "بلا معاوضہ مہارت کا کھیل منتخب کریں۔ مشکل سطح پر درست جواب کے زیادہ ڈائمنڈز ہیں؛ ان کی نقد قیمت نہیں۔",
    game_expired: "یہ چیلنج ختم ہو گیا۔ /games سے نیا شروع کریں۔",
    game_used: "یہ چیلنج پہلے جمع کیا جا چکا ہے۔",
    game_wrong: "جواب درست نہیں۔ کوئی ڈائمنڈ نہیں کٹے؛ دوسرا چیلنج آزمائیں۔",
    game_correct: "درست۔ +{reward} ڈائمنڈز۔ بیلنس: {balance}۔",
    daily_done: "آج کا انعام پہلے ہی لیا جا چکا ہے۔",
    daily_claim:
      "آج کا انعام: +{reward} ڈائمنڈز۔ مسلسل دن: {streak}۔ بیلنس: {balance}۔",
    profile:
      "ڈائمنڈز: {diamonds}\nلیول: {level}\nمسلسل دن: {streak}\nپریمیم مطالعے کے کریڈٹ: {credits}\nکردار: {persona}",
    no_reading:
      "ابھی کوئی محفوظ مطالعہ موجود نہیں۔ /menu سے مطالعہ منتخب کریں۔",
    leaderboard: "گمنام لیڈر بورڈ (صرف ڈائمنڈز):\n{rows}\n\nآپ کا مقام: {rank}",
    leaderboard_empty: "لیڈر بورڈ ابھی خالی ہے۔",
    personas:
      "کردار منتخب کریں۔ نام صرف غیر جانب دار انداز کے labels ہیں، کردار کی نقل نہیں۔",
    persona_saved: "کردار محفوظ ہو گیا: {persona}۔",
    charity:
      "اختیاری مہم: کوئی حوصلہ افزا بات کہیں یا اپنی پسند کے مقصد کی مدد کریں—صرف اگر آپ چاہیں۔ عطیہ یا ثبوت درکار نہیں۔",
    quest_claimed: "مہم مکمل: +{reward} ڈائمنڈز۔ بیلنس: {balance}۔",
    quest_duplicate: "آپ آج یہ اختیاری مہم پہلے مکمل کر چکے ہیں۔",
    palm_photo:
      "اس ورژن میں ہاتھ کی تصاویر کا تجزیہ یا محفوظ نہیں کیا جاتا۔ موضوع کے مطابق تحریری غور کے لیے /palm استعمال کریں۔",
    premium_unavailable:
      "پریمیم کریڈٹ ابھی استعمال نہیں ہو سکا۔ اگر درخواست مکمل نہیں ہوئی تو بیلنس تبدیل نہیں ہوا؛ بعد میں /palm آزمائیں۔",
  },
};

const QUEST_LABELS: Record<Language, Array<[string, string]>> = {
  en: [["Kindness", "kindness"], ["Gratitude", "gratitude"], [
    "Helpful act",
    "helpful",
  ]],
  ur: [["مہربانی", "kindness"], ["شکرگزاری", "gratitude"], [
    "مددگار کام",
    "helpful",
  ]],
};
const GAME_LABELS: Record<Language, Record<"easy" | "hard", string>> = {
  en: { easy: "Easy", hard: "Hard" },
  ur: { easy: "آسان", hard: "مشکل" },
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

function constantTimeEqual(left: string, right: string): boolean {
  const encoder = new TextEncoder();
  const a = encoder.encode(left);
  const b = encoder.encode(right);
  const length = Math.max(a.length, b.length);
  let diff = a.length ^ b.length;
  for (let i = 0; i < length; i++) diff |= (a[i] ?? 0) ^ (b[i] ?? 0);
  return diff === 0;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function privateUserId(value: unknown): number | null {
  if (!Number.isSafeInteger(value) || typeof value !== "number" || value <= 0) {
    return null;
  }
  return value;
}

function isValidPreCheckout(value: unknown): value is TelegramPreCheckout {
  return isRecord(value) && typeof value.id === "string" &&
    value.id.length > 0 && value.id.length <= 256 &&
    isRecord(value.from) && privateUserId(value.from.id) !== null &&
    typeof value.invoice_payload === "string" &&
    value.invoice_payload.length > 0 && value.invoice_payload.length <= 128 &&
    Number.isSafeInteger(value.total_amount) &&
    (value.total_amount as number) > 0 && value.currency === "XTR";
}

function isValidCallback(value: unknown): value is TelegramCallback {
  if (
    !isRecord(value) || typeof value.id !== "string" || value.id.length === 0 ||
    value.id.length > 256 || !isRecord(value.from) ||
    privateUserId(value.from.id) === null || typeof value.data !== "string" ||
    value.data.length > 64 || !isRecord(value.message) ||
    !isRecord(value.message.chat)
  ) return false;
  return value.message.chat.type === "private" &&
    Number.isSafeInteger(value.message.chat.id);
}

function isValidSuccessfulPayment(
  value: unknown,
): value is NonNullable<TelegramMessage["successful_payment"]> {
  return isRecord(value) && typeof value.invoice_payload === "string" &&
    value.invoice_payload.length > 0 && value.invoice_payload.length <= 128 &&
    typeof value.telegram_payment_charge_id === "string" &&
    value.telegram_payment_charge_id.length > 0 &&
    value.telegram_payment_charge_id.length <= 255 &&
    Number.isSafeInteger(value.total_amount) &&
    (value.total_amount as number) > 0 && value.currency === "XTR";
}

function format(
  template: string,
  values: Record<string, string | number>,
): string {
  return template.replace(
    /\{([a-z_]+)\}/g,
    (_whole, key: string) => String(values[key] ?? ""),
  );
}

function focusKeyboard(
  mode: "basic" | "buy" | "use",
  lang: Language,
): Keyboard {
  const labels = lang === "en"
    ? ["general", "relationships", "work", "personal growth"]
    : ["عمومی", "رشتے", "کام", "ذاتی ترقی"];
  const values: Focus[] = ["general", "love", "work", "growth"];
  return {
    inline_keyboard: [[
      { text: labels[0], callback_data: `palm:focus:${mode}:${values[0]}` },
      { text: labels[1], callback_data: `palm:focus:${mode}:${values[1]}` },
    ], [
      { text: labels[2], callback_data: `palm:focus:${mode}:${values[2]}` },
      { text: labels[3], callback_data: `palm:focus:${mode}:${values[3]}` },
    ]],
  };
}

function mainKeyboard(lang: Language): Keyboard {
  const rows = lang === "en"
    ? [
      ["Fortune", "f8:fortune", "Tarot", "f8:tarot"],
      ["Basic palm", "f8:palm_basic", "Premium palm", "f8:palm_premium"],
      ["Horoscope", "f8:horoscope", "Games", "f8:games"],
      ["Daily reward", "f8:daily", "Leaderboard", "f8:leaderboard"],
      ["Personas", "f8:personas", "Charity quest", "f8:charity"],
      ["Language / زبان", "f8:language", "Profile", "f8:profile"],
    ]
    : [
      ["قسمت", "f8:fortune", "ٹیرو", "f8:tarot"],
      ["بنیادی ہتھیلی", "f8:palm_basic", "پریمیم ہتھیلی", "f8:palm_premium"],
      ["زائچہ", "f8:horoscope", "کھیل", "f8:games"],
      ["روزانہ انعام", "f8:daily", "لیڈر بورڈ", "f8:leaderboard"],
      ["کردار", "f8:personas", "نیکی کی مہم", "f8:charity"],
      ["زبان / Language", "f8:language", "پروفائل", "f8:profile"],
    ];
  return {
    inline_keyboard: rows.map(([text1, data1, text2, data2]) => [
      { text: text1, callback_data: data1 },
      { text: text2, callback_data: data2 },
    ]),
  };
}

function languageKeyboard(): Keyboard {
  return {
    inline_keyboard: [[
      { text: "English", callback_data: "lang:en" },
      { text: "اردو", callback_data: "lang:ur" },
    ]],
  };
}

function parseHoroscopeArgs(
  args: string,
): { date: string; time: string; location: string } | null {
  const match = /^(\d{4}-\d{2}-\d{2})\s+([0-2]\d:[0-5]\d)\s*,?\s*(.{1,120})$/
    .exec(args.trim());
  if (!match || !/^([01]\d|2[0-3]):[0-5]\d$/.test(match[2])) return null;
  const dateText = match[1];
  const date = new Date(`${dateText}T00:00:00Z`);
  if (
    !Number.isFinite(date.getTime()) ||
    date.toISOString().slice(0, 10) !== dateText
  ) return null;
  if (dateText < "1900-01-01") return null;
  return {
    date: dateText,
    time: match[2],
    location: match[3].trim().replace(/\s+/g, " "),
  };
}

function safeString(value: unknown, max = 3500): string {
  return typeof value === "string" ? value.slice(0, max) : "";
}

export function createWebhookHandler(
  deps: HandlerDependencies,
): (request: Request) => Promise<Response> {
  const fetcher = deps.fetcher ?? fetch;
  const now = deps.now ?? (() => new Date());
  return async (request: Request): Promise<Response> => {
    if (request.method !== "POST") {
      return jsonResponse({ error: "method_not_allowed" }, 405);
    }
    const secrets = requiredSecrets(deps.env);
    if (!secrets) {
      return jsonResponse({ error: "function_not_configured" }, 503);
    }
    const supplied = request.headers.get("X-Telegram-Bot-Api-Secret-Token") ??
      "";
    if (!constantTimeEqual(supplied, secrets.webhookSecret)) {
      return jsonResponse({ error: "unauthorized" }, 401);
    }
    const declaredLength = Number(request.headers.get("content-length") ?? "0");
    if (declaredLength > 256_000) {
      return jsonResponse({ error: "payload_too_large" }, 413);
    }
    let raw: string;
    try {
      raw = await request.text();
      if (new TextEncoder().encode(raw).length > 256_000) {
        return jsonResponse({ error: "payload_too_large" }, 413);
      }
    } catch {
      return jsonResponse({ error: "invalid_request" }, 400);
    }
    let update: unknown;
    try {
      update = JSON.parse(raw) as unknown;
    } catch {
      return jsonResponse({ error: "invalid_json" }, 400);
    }
    if (
      !isRecord(update) || !Number.isSafeInteger(update.update_id) ||
      (update.update_id as number) < 0
    ) {
      return jsonResponse({ error: "invalid_update" }, 400);
    }
    const store = new Fortunis8Store(
      secrets.supabaseUrl,
      secrets.serviceKey,
      fetcher,
    );
    const telegram = new TelegramApi(secrets.botToken, fetcher);
    try {
      await processUpdate(
        update as unknown as TelegramUpdate,
        store,
        telegram,
        secrets.price,
        now,
      );
      return jsonResponse({ ok: true });
    } catch {
      // Never log request bodies, Telegram tokens, webhook secrets, database keys, or provider errors.
      console.error("Fortunis8 webhook update failed.");
      return jsonResponse({ error: "processing_failed" }, 500);
    }
  };
}

class TelegramApi {
  readonly #token: string;
  readonly #fetch: Fetcher;
  constructor(token: string, fetcher: Fetcher) {
    this.#token = token;
    this.#fetch = fetcher;
  }

  async call(method: string, payload: JsonRecord): Promise<unknown> {
    let response: Response;
    try {
      response = await this.#fetch(
        `https://api.telegram.org/bot${this.#token}/${method}`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(payload),
          signal: AbortSignal.timeout(8_000),
        },
      );
      if (!response.ok) throw new Error("telegram_failed");
      const result = await response.json() as {
        ok?: boolean;
        result?: unknown;
      };
      if (!result?.ok) throw new Error("telegram_failed");
      return result.result;
    } catch {
      throw new Error("telegram_failed");
    }
  }

  async sendMessage(
    chatId: number,
    text: string,
    replyMarkup?: Keyboard,
  ): Promise<void> {
    const payload: JsonRecord = {
      chat_id: chatId,
      text: text.slice(0, 4096),
      disable_web_page_preview: true,
    };
    if (replyMarkup?.inline_keyboard.length) payload.reply_markup = replyMarkup;
    await this.call("sendMessage", payload);
  }

  async answerCallback(queryId: string): Promise<void> {
    await this.call("answerCallbackQuery", { callback_query_id: queryId });
  }

  async answerPreCheckout(
    query: TelegramPreCheckout,
    ok: boolean,
    error?: string,
  ): Promise<void> {
    await this.answerPreCheckoutById(query.id, ok, error);
  }

  async answerPreCheckoutById(
    queryId: string,
    ok: boolean,
    error?: string,
  ): Promise<void> {
    const payload: JsonRecord = { pre_checkout_query_id: queryId, ok };
    if (!ok && error) payload.error_message = error.slice(0, 200);
    await this.call("answerPreCheckoutQuery", payload);
  }

  async sendInvoice(
    chatId: number,
    payload: string,
    price: number,
    lang: Language,
  ): Promise<void> {
    await this.call("sendInvoice", {
      chat_id: chatId,
      title: lang === "en"
        ? "Detailed palm-themed reflection"
        : "ہتھیلی سے متاثر تفصیلی غور",
      description: lang === "en"
        ? `One entertainment-only text reading for ${price} Telegram Stars.`
        : `${price} Telegram Stars میں ایک تفریحی تحریری مطالعہ۔`,
      payload,
      provider_token: "",
      currency: "XTR",
      prices: [{
        label: lang === "en" ? "Detailed reading" : "تفصیلی مطالعہ",
        amount: price,
      }],
    });
  }
}

async function processUpdate(
  update: TelegramUpdate,
  store: Fortunis8Store,
  telegram: TelegramApi,
  price: number,
  now: () => Date,
): Promise<void> {
  const raw = update as unknown as Record<string, unknown>;
  if (raw.pre_checkout_query !== undefined) {
    if (!isValidPreCheckout(raw.pre_checkout_query)) {
      if (
        isRecord(raw.pre_checkout_query) &&
        typeof raw.pre_checkout_query.id === "string" &&
        raw.pre_checkout_query.id.length > 0 &&
        raw.pre_checkout_query.id.length <= 256
      ) {
        await telegram.answerPreCheckoutById(
          raw.pre_checkout_query.id,
          false,
          "Invalid checkout request. No payment was taken.",
        );
      }
      return;
    }
    await handlePreCheckout(raw.pre_checkout_query, store, telegram);
    return;
  }
  if (raw.callback_query !== undefined) {
    if (!isValidCallback(raw.callback_query)) {
      if (
        isRecord(raw.callback_query) &&
        typeof raw.callback_query.id === "string" &&
        raw.callback_query.id.length > 0 &&
        raw.callback_query.id.length <= 256
      ) await telegram.answerCallback(raw.callback_query.id);
      return;
    }
    await handleCallback(
      raw.callback_query,
      store,
      telegram,
      price,
      update.update_id,
    );
    return;
  }
  if (raw.message !== undefined && isRecord(raw.message)) {
    await handleMessage(
      raw.message as unknown as TelegramMessage,
      store,
      telegram,
      price,
      update.update_id,
      now,
    );
  }
}

async function handlePreCheckout(
  query: TelegramPreCheckout,
  store: Fortunis8Store,
  telegram: TelegramApi,
): Promise<void> {
  const userId = privateUserId(query.from?.id);
  if (!userId) {
    await telegram.answerPreCheckout(query, false, "Invalid user.");
    return;
  }
  try {
    const invoice = await store.validInvoice(query.invoice_payload, userId);
    const valid = Boolean(
      invoice && invoice.currency === "XTR" &&
        invoice.amount_stars === query.total_amount && query.currency === "XTR",
    );
    await telegram.answerPreCheckout(
      query,
      valid,
      valid
        ? undefined
        : "This invoice is invalid or expired. No payment was taken.",
    );
  } catch {
    const language = await store.getOrCreateLanguage(userId).catch(() =>
      "en" as Language
    );
    await telegram.answerPreCheckout(
      query,
      false,
      COPY[language].payment_unavailable,
    );
  }
}

async function handleMessage(
  message: TelegramMessage,
  store: Fortunis8Store,
  telegram: TelegramApi,
  price: number,
  updateId: number,
  now: () => Date,
): Promise<void> {
  const userId = privateUserId(message.from?.id);
  if (!userId) return;
  const chatId = message.chat?.id;
  if (!Number.isSafeInteger(chatId)) return;
  if (message.chat.type !== "private") {
    if (message.text?.startsWith("/")) {
      await telegram.sendMessage(chatId, COPY.en.private_only);
    }
    return;
  }
  const language = await store.getOrCreateLanguage(userId);
  if (message.successful_payment !== undefined) {
    if (!isValidSuccessfulPayment(message.successful_payment)) {
      await telegram.sendMessage(chatId, COPY[language].payment_invalid);
      return;
    }
    await handlePayment(
      userId,
      chatId,
      language,
      message.successful_payment,
      store,
      telegram,
      updateId,
    );
    return;
  }
  if (Array.isArray(message.photo) && message.photo.length) {
    await telegram.sendMessage(chatId, COPY[language].palm_photo);
    return;
  }
  const text = message.text?.trim() ?? "";
  if (!text) return;
  const command = /^\/([a-z_]+)(?:@[a-z0-9_]+)?(?:\s+([\s\S]*))?$/i.exec(text);
  if (!command) {
    if (
      language === "ur" &&
      /(قسمت|زائچہ|ٹیرو|پروفائل|روزانہ انعام|خیرات)/.test(text)
    ) {
      if (text.includes("ٹیرو")) {
        await showTarot(userId, chatId, language, updateId, store, telegram);
      } else if (text.includes("پروفائل")) {
        await showProfile(userId, chatId, language, store, telegram);
      } else if (text.includes("روزانہ انعام")) {
        await claimDaily(userId, chatId, language, store, telegram);
      } else if (text.includes("خیرات")) {
        await showCharity(chatId, language, telegram);
      } else {await showFortune(
          userId,
          chatId,
          language,
          updateId,
          now,
          store,
          telegram,
        );}
    }
    return;
  }
  const name = command[1].toLowerCase();
  const args = command[2] ?? "";
  switch (name) {
    case "start":
      await store.ensureAccount(userId);
      await telegram.sendMessage(
        chatId,
        COPY[language].welcome,
        languageKeyboard(),
      );
      await telegram.sendMessage(
        chatId,
        COPY[language].menu,
        mainKeyboard(language),
      );
      break;
    case "menu":
      await telegram.sendMessage(
        chatId,
        COPY[language].menu,
        mainKeyboard(language),
      );
      break;
    case "help":
      await telegram.sendMessage(chatId, COPY[language].help);
      break;
    case "fortune":
      await showFortune(
        userId,
        chatId,
        language,
        updateId,
        now,
        store,
        telegram,
      );
      break;
    case "tarot":
      await showTarot(userId, chatId, language, updateId, store, telegram);
      break;
    case "horoscope":
      await showHoroscope(userId, chatId, language, args, store, telegram);
      break;
    case "palm":
      await showPalmStart(userId, chatId, language, price, store, telegram);
      break;
    case "games":
      await telegram.sendMessage(
        chatId,
        COPY[language].game_choose,
        gameMenuKeyboard(language),
      );
      break;
    case "daily":
    case "reward":
      await claimDaily(userId, chatId, language, store, telegram);
      break;
    case "profile":
      await showProfile(userId, chatId, language, store, telegram);
      break;
    case "leaderboard":
      await showLeaderboard(userId, chatId, language, store, telegram);
      break;
    case "personas":
    case "personalize":
      await showPersonas(chatId, language, telegram);
      break;
    case "charity":
    case "quests":
      await showCharity(chatId, language, telegram);
      break;
    case "last":
      await showLast(userId, chatId, language, store, telegram);
      break;
    case "cancel":
      await telegram.sendMessage(
        chatId,
        language === "en"
          ? "Nothing is being collected. Horoscope details are accepted only in one command."
          : "کوئی معلومات جمع نہیں کی جا رہیں۔ زائچے کی تفصیل صرف ایک مکمل کمانڈ میں قبول ہوتی ہے۔",
      );
      break;
    default:
      break;
  }
}

async function showFortune(
  userId: number,
  chatId: number,
  lang: Language,
  _updateId: number,
  now: () => Date,
  store: Fortunis8Store,
  telegram: TelegramApi,
): Promise<void> {
  const account = await store.account(userId);
  const day = now().toISOString().slice(0, 10);
  const content = withPersona(
    await fortune(lang, `fortune:${userId}:${day}`),
    String(account.selected_persona),
    lang,
  );
  // The schema's allowed reading types do not include "fortune"; keep its existing "horoscope" category.
  await store.saveReading(userId, "horoscope", "Fortune", content, {
    source: "fortune",
  });
  await telegram.sendMessage(chatId, content);
}

async function showTarot(
  userId: number,
  chatId: number,
  lang: Language,
  updateId: number,
  store: Fortunis8Store,
  telegram: TelegramApi,
): Promise<void> {
  const account = await store.account(userId);
  const content = withPersona(
    await tarot(lang, `tarot:${userId}:${updateId}`),
    String(account.selected_persona),
    lang,
  );
  await store.saveReading(userId, "tarot", "Tarot guidance", content);
  await telegram.sendMessage(chatId, content);
}

async function showHoroscope(
  userId: number,
  chatId: number,
  lang: Language,
  args: string,
  store: Fortunis8Store,
  telegram: TelegramApi,
): Promise<void> {
  const parsed = parseHoroscopeArgs(args);
  if (!parsed) {
    await telegram.sendMessage(
      chatId,
      args ? COPY[lang].horoscope_invalid : COPY[lang].horoscope_prompt,
    );
    return;
  }
  if (parsed.date > new Date().toISOString().slice(0, 10)) {
    await telegram.sendMessage(chatId, COPY[lang].horoscope_future);
    return;
  }
  const account = await store.account(userId);
  const reading = await horoscopeReading(
    parsed.date,
    parsed.time,
    parsed.location,
    lang,
  );
  const content = withPersona(
    reading.content,
    String(account.selected_persona),
    lang,
  );
  // Birth date, time, and city are transient; only the non-identifying sun-sign label is stored.
  await store.saveReading(
    userId,
    "horoscope",
    "Horoscope-style reading",
    content,
    { sun_sign: reading.sign },
  );
  await telegram.sendMessage(chatId, content);
}

async function showPalmStart(
  userId: number,
  chatId: number,
  lang: Language,
  price: number,
  store: Fortunis8Store,
  telegram: TelegramApi,
): Promise<void> {
  const account = await store.account(userId);
  const credits = Number(account.premium_reading_credits ?? 0);
  const mode = credits > 0 ? "use" : "buy";
  const prompt = mode === "use"
    ? `${format(COPY[lang].credits_available, { credits })}\n${
      COPY[lang].focus
    }`
    : `${format(COPY[lang].premium_price, { price })}\n${COPY[lang].focus}`;
  await telegram.sendMessage(chatId, prompt, focusKeyboard(mode, lang));
}

async function showBasicPalm(
  userId: number,
  chatId: number,
  lang: Language,
  focus: Focus,
  store: Fortunis8Store,
  telegram: TelegramApi,
): Promise<void> {
  const account = await store.account(userId);
  const content = withPersona(
    palmReading(focus, lang),
    String(account.selected_persona),
    lang,
  );
  await store.saveReading(
    userId,
    "palm_basic",
    COPY[lang].basic_title,
    content,
    { focus },
  );
  await telegram.sendMessage(chatId, content);
}

async function sendStarsInvoice(
  userId: number,
  chatId: number,
  lang: Language,
  focus: Focus,
  price: number,
  store: Fortunis8Store,
  telegram: TelegramApi,
): Promise<void> {
  const payload = `fortunis8:${userId}:${crypto.randomUUID()}`;
  await store.createInvoice(userId, focus, price, payload);
  try {
    await telegram.sendInvoice(chatId, payload, price, lang);
  } catch {
    await store.cancelInvoice(userId, payload).catch(() => undefined);
    throw new Error("invoice_delivery_failed");
  }
}

async function redeemPremium(
  userId: number,
  updateId: number,
  chatId: number,
  lang: Language,
  focus: Focus,
  store: Fortunis8Store,
  telegram: TelegramApi,
): Promise<void> {
  const account = await store.account(userId);
  const content = withPersona(
    palmReading(focus, lang, true),
    String(account.selected_persona),
    lang,
  );
  const result = await store.redeemPremium(
    userId,
    updateId,
    focus,
    COPY[lang].premium_title,
    content,
  );
  if (result.duplicate === true) {
    await telegram.sendMessage(chatId, COPY[lang].premium_update_duplicate);
    return;
  }
  if (result.ok !== true) {
    await telegram.sendMessage(chatId, COPY[lang].premium_unavailable);
    return;
  }
  await telegram.sendMessage(chatId, content);
  await telegram.sendMessage(
    chatId,
    format(COPY[lang].payment_credit, {
      credits: Number(result.credits_remaining ?? 0),
    }),
  );
}

async function handlePayment(
  userId: number,
  chatId: number,
  lang: Language,
  payment: NonNullable<TelegramMessage["successful_payment"]>,
  store: Fortunis8Store,
  telegram: TelegramApi,
  updateId: number,
): Promise<void> {
  const result = await store.recordPayment(
    userId,
    payment.invoice_payload,
    payment.telegram_payment_charge_id,
    payment.total_amount,
    payment.currency,
  );
  if (result.ok !== true) {
    await telegram.sendMessage(chatId, COPY[lang].payment_invalid);
    return;
  }
  if (result.credited !== true) {
    await telegram.sendMessage(
      chatId,
      result.duplicate
        ? COPY[lang].payment_duplicate
        : COPY[lang].payment_pending,
    );
    return;
  }
  const focus = parseFocus(String(result.focus ?? ""));
  if (!focus) {
    await telegram.sendMessage(chatId, COPY[lang].payment_pending);
    return;
  }
  try {
    await redeemPremium(userId, updateId, chatId, lang, focus, store, telegram);
  } catch {
    // The Stars ledger and credit are already committed. Let the user recover through /palm.
    await telegram.sendMessage(chatId, COPY[lang].payment_pending);
  }
}

async function handleCallback(
  query: TelegramCallback,
  store: Fortunis8Store,
  telegram: TelegramApi,
  price: number,
  updateId: number,
): Promise<void> {
  await telegram.answerCallback(query.id);
  const userId = privateUserId(query.from?.id);
  const message = query.message;
  if (
    !userId || !message || message.chat?.type !== "private" ||
    !Number.isSafeInteger(message.chat.id)
  ) return;
  const chatId = message.chat.id;
  const lang = await store.getOrCreateLanguage(userId);
  const data = query.data ?? "";
  if (data === "lang:en" || data === "lang:ur") {
    const selected = data.slice(5) as Language;
    await store.setLanguage(userId, selected);
    await store.ensureAccount(userId);
    await telegram.sendMessage(
      chatId,
      COPY[selected].language_saved,
      mainKeyboard(selected),
    );
    return;
  }
  if (data === "f8:language") {
    await telegram.sendMessage(chatId, COPY[lang].welcome, languageKeyboard());
  } else if (data === "f8:fortune") {
    await showFortune(
      userId,
      chatId,
      lang,
      updateId,
      () => new Date(),
      store,
      telegram,
    );
  } else if (data === "f8:tarot") {
    await showTarot(userId, chatId, lang, updateId, store, telegram);
  } else if (data === "f8:palm_basic") {
    await telegram.sendMessage(
      chatId,
      COPY[lang].focus,
      focusKeyboard("basic", lang),
    );
  } else if (data === "f8:palm_premium") {
    await showPalmStart(userId, chatId, lang, price, store, telegram);
  } else if (data === "f8:horoscope") {
    await telegram.sendMessage(chatId, COPY[lang].horoscope_prompt);
  } else if (data === "f8:games") {
    await telegram.sendMessage(
      chatId,
      COPY[lang].game_choose,
      gameMenuKeyboard(lang),
    );
  } else if (data === "f8:daily") {
    await claimDaily(userId, chatId, lang, store, telegram);
  } else if (data === "f8:profile") {
    await showProfile(userId, chatId, lang, store, telegram);
  } else if (data === "f8:leaderboard") {
    await showLeaderboard(userId, chatId, lang, store, telegram);
  } else if (data === "f8:personas") {
    await showPersonas(chatId, lang, telegram);
  } else if (data === "f8:charity") {
    await showCharity(chatId, lang, telegram);
  } else if (data.startsWith("palm:focus:")) {
    const [, , mode, focusText] = data.split(":");
    const focus = parseFocus(focusText ?? "");
    if (!focus) return;
    if (mode === "basic") {
      await showBasicPalm(userId, chatId, lang, focus, store, telegram);
    } else if (mode === "buy") {
      await sendStarsInvoice(
        userId,
        chatId,
        lang,
        focus,
        price,
        store,
        telegram,
      );
    } else if (mode === "use") {
      await redeemPremium(
        userId,
        updateId,
        chatId,
        lang,
        focus,
        store,
        telegram,
      );
    }
  } else if (data === "game:easy" || data === "game:hard") {
    await startGame(
      userId,
      chatId,
      lang,
      data.slice(5) as "easy" | "hard",
      store,
      telegram,
    );
  } else if (data.startsWith("answer:")) {
    await submitGameAnswer(userId, chatId, lang, data, store, telegram);
  } else if (data.startsWith("persona:")) {
    const name = data.slice("persona:".length);
    if (PERSONAS.includes(name as Persona)) {
      await store.setPersona(userId, name as Persona);
      await telegram.sendMessage(
        chatId,
        format(COPY[lang].persona_saved, { persona: name }),
      );
    }
  } else if (data.startsWith("quest:")) {
    await claimQuest(
      userId,
      chatId,
      lang,
      data.slice("quest:".length),
      store,
      telegram,
    );
  }
}

function gameMenuKeyboard(lang: Language): Keyboard {
  return {
    inline_keyboard: [[
      { text: GAME_LABELS[lang].easy, callback_data: "game:easy" },
      { text: GAME_LABELS[lang].hard, callback_data: "game:hard" },
    ]],
  };
}

async function startGame(
  userId: number,
  chatId: number,
  lang: Language,
  difficulty: "easy" | "hard",
  store: Fortunis8Store,
  telegram: TelegramApi,
): Promise<void> {
  const game = GAME[lang][difficulty];
  const sessionId = crypto.randomUUID();
  await store.createGame(
    userId,
    sessionId,
    difficulty,
    game.question,
    [...game.options],
    game.answer,
    game.reward,
  );
  await telegram.sendMessage(
    chatId,
    `${GAME_LABELS[lang][difficulty]} challenge: ${game.question}`,
    {
      inline_keyboard: [
        game.options.map((option) => ({
          text: option,
          callback_data: `answer:${sessionId}:${option}`,
        })),
      ],
    },
  );
}

async function submitGameAnswer(
  userId: number,
  chatId: number,
  lang: Language,
  data: string,
  store: Fortunis8Store,
  telegram: TelegramApi,
): Promise<void> {
  const match = /^answer:([0-9a-f-]{36}):([^:]{1,50})$/i.exec(data);
  if (!match) return;
  const result = await store.completeGame(userId, match[1], match[2]);
  if (result.reason === "expired") {
    await telegram.sendMessage(chatId, COPY[lang].game_expired);
  } else if (
    result.reason === "not_found" ||
    (result.completed === true && result.correct === true &&
      Number(result.reward) === 0)
  ) await telegram.sendMessage(chatId, COPY[lang].game_used);
  else if (result.correct === true) {
    await telegram.sendMessage(
      chatId,
      format(COPY[lang].game_correct, {
        reward: Number(result.reward ?? 0),
        balance: Number(result.diamonds ?? 0),
      }),
    );
  } else if (result.ok === true) {
    await telegram.sendMessage(chatId, COPY[lang].game_wrong);
  } else await telegram.sendMessage(chatId, COPY[lang].unavailable);
}

async function claimDaily(
  userId: number,
  chatId: number,
  lang: Language,
  store: Fortunis8Store,
  telegram: TelegramApi,
): Promise<void> {
  const result = await store.claimDaily(userId);
  if (result.ok !== true) {
    return await telegram.sendMessage(chatId, COPY[lang].unavailable);
  }
  if (result.claimed === true) {
    await telegram.sendMessage(
      chatId,
      format(COPY[lang].daily_claim, {
        reward: Number(result.reward ?? 0),
        streak: Number(result.streak ?? 0),
        balance: Number(result.diamonds ?? 0),
      }),
    );
  } else await telegram.sendMessage(chatId, COPY[lang].daily_done);
}

async function showProfile(
  userId: number,
  chatId: number,
  lang: Language,
  store: Fortunis8Store,
  telegram: TelegramApi,
): Promise<void> {
  const account = await store.account(userId);
  await telegram.sendMessage(
    chatId,
    format(COPY[lang].profile, {
      diamonds: Number(account.diamonds ?? 0),
      level: Number(account.level ?? 1),
      streak: Number(account.streak_count ?? 0),
      credits: Number(account.premium_reading_credits ?? 0),
      persona: String(account.selected_persona ?? "Wizard"),
    }),
  );
}

async function showLast(
  userId: number,
  chatId: number,
  lang: Language,
  store: Fortunis8Store,
  telegram: TelegramApi,
): Promise<void> {
  const reading = await store.lastReading(userId);
  if (!reading) {
    return await telegram.sendMessage(chatId, COPY[lang].no_reading);
  }
  await telegram.sendMessage(
    chatId,
    `${safeString(reading.title, 120)}\n\n${safeString(reading.content)}`,
  );
}

async function showLeaderboard(
  userId: number,
  chatId: number,
  lang: Language,
  store: Fortunis8Store,
  telegram: TelegramApi,
): Promise<void> {
  const { scores, rank } = await store.leaderboard(userId);
  if (!scores.length) {
    return await telegram.sendMessage(chatId, COPY[lang].leaderboard_empty);
  }
  const rows = scores.map((score, index) => `#${index + 1} — ${score}`).join(
    "\n",
  );
  const rankText = rank === null
    ? (lang === "en" ? "not ranked" : "درج نہیں")
    : `#${rank}`;
  await telegram.sendMessage(
    chatId,
    format(COPY[lang].leaderboard, { rows, rank: rankText }),
  );
}

async function showPersonas(
  chatId: number,
  lang: Language,
  telegram: TelegramApi,
): Promise<void> {
  const rows: Button[][] = [];
  for (let i = 0; i < PERSONAS.length; i += 3) {
    rows.push(
      PERSONAS.slice(i, i + 3).map((name) => ({
        text: name,
        callback_data: `persona:${name}`,
      })),
    );
  }
  await telegram.sendMessage(chatId, COPY[lang].personas, {
    inline_keyboard: rows,
  });
}

async function showCharity(
  chatId: number,
  lang: Language,
  telegram: TelegramApi,
): Promise<void> {
  const labels = QUEST_LABELS[lang].map(([text, key]) => ({
    text,
    callback_data: `quest:${key}`,
  }));
  await telegram.sendMessage(chatId, COPY[lang].charity, {
    inline_keyboard: [labels],
  });
}

async function claimQuest(
  userId: number,
  chatId: number,
  lang: Language,
  key: string,
  store: Fortunis8Store,
  telegram: TelegramApi,
): Promise<void> {
  const result = await store.claimQuest(userId, key);
  if (result.claimed === true) {
    await telegram.sendMessage(
      chatId,
      format(COPY[lang].quest_claimed, {
        reward: Number(result.reward ?? 0),
        balance: Number(result.diamonds ?? 0),
      }),
    );
  } else if (result.ok === true) {
    await telegram.sendMessage(chatId, COPY[lang].quest_duplicate);
  } else await telegram.sendMessage(chatId, COPY[lang].unavailable);
}
