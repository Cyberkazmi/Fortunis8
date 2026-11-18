import type { Focus, Language, Persona } from "./domain.ts";

export type JsonRecord = Record<string, unknown>;
export type Fetcher = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>;

export class StoreError extends Error {
  constructor() {
    super("Fortunis8 persistence request failed.");
    this.name = "StoreError";
  }
}

function apiKeyFromEnvironment(
  env: (name: string) => string | undefined,
): string | undefined {
  const legacy = env("SUPABASE_SERVICE_ROLE_KEY");
  if (legacy) return legacy;
  const keysJson = env("SUPABASE_SECRET_KEYS");
  if (keysJson) {
    try {
      const keys = JSON.parse(keysJson) as Record<string, unknown>;
      const defaultKey = keys.default;
      if (typeof defaultKey === "string" && defaultKey) return defaultKey;
    } catch {
      // Fail closed below; do not log environment contents.
    }
  }
  return undefined;
}

export function requiredSecrets(env: (name: string) => string | undefined) {
  const supabaseUrl = env("SUPABASE_URL")?.replace(/\/$/, "");
  const serviceKey = apiKeyFromEnvironment(env);
  const botToken = env("TELEGRAM_BOT_TOKEN");
  const webhookSecret = env("TELEGRAM_WEBHOOK_SECRET");
  const priceText = env("PREMIUM_PALM_PRICE_STARS") ?? "25";
  const price = Number(priceText);
  if (
    !supabaseUrl || !/^https:\/\//i.test(supabaseUrl) || !serviceKey ||
    !botToken || !webhookSecret
  ) return null;
  if (!Number.isInteger(price) || price < 1 || price > 1000) return null;
  if (!/^[A-Za-z0-9_-]{32,256}$/.test(webhookSecret)) return null;
  return { supabaseUrl, serviceKey, botToken, webhookSecret, price };
}

export class Fortunis8Store {
  readonly #baseUrl: string;
  readonly #serviceKey: string;
  readonly #fetch: Fetcher;

  constructor(supabaseUrl: string, serviceKey: string, fetcher: Fetcher) {
    this.#baseUrl = `${supabaseUrl.replace(/\/$/, "")}/rest/v1/`;
    this.#serviceKey = serviceKey;
    this.#fetch = fetcher;
  }

  async #request(path: string, init: RequestInit = {}): Promise<unknown> {
    const headers = new Headers(init.headers);
    headers.set("apikey", this.#serviceKey);
    headers.set("Authorization", `Bearer ${this.#serviceKey}`);
    headers.set("Accept", "application/json");
    if (init.body !== undefined) {
      headers.set("Content-Type", "application/json");
    }
    try {
      const response = await this.#fetch(new URL(path, this.#baseUrl), {
        ...init,
        headers,
        signal: AbortSignal.timeout(7_000),
      });
      if (!response.ok) throw new StoreError();
      if (response.status === 204) return null;
      const text = await response.text();
      if (!text) return null;
      try {
        return JSON.parse(text) as unknown;
      } catch {
        throw new StoreError();
      }
    } catch {
      throw new StoreError();
    }
  }

  async #rpc(name: string, payload: JsonRecord): Promise<unknown> {
    return await this.#request(`rpc/${name}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async getOrCreateLanguage(userId: number): Promise<Language> {
    const query = new URLSearchParams({
      select: "language",
      telegram_user_id: `eq.${userId}`,
      limit: "1",
    });
    const rows = await this.#request(`fortunis8_users?${query}`) as Array<
      JsonRecord
    >;
    if (Array.isArray(rows) && rows.length) {
      const language = rows[0]?.language;
      if (language === "en" || language === "ur") return language;
      throw new StoreError();
    }
    const upsert = new URLSearchParams({ on_conflict: "telegram_user_id" });
    await this.#request(`fortunis8_users?${upsert}`, {
      method: "POST",
      headers: { Prefer: "resolution=ignore-duplicates,return=minimal" },
      body: JSON.stringify({ telegram_user_id: userId }),
    });
    return await this.getOrCreateLanguage(userId);
  }

  async setLanguage(userId: number, language: Language): Promise<void> {
    await this.getOrCreateLanguage(userId);
    const query = new URLSearchParams({ telegram_user_id: `eq.${userId}` });
    await this.#request(`fortunis8_users?${query}`, {
      method: "PATCH",
      headers: { Prefer: "return=minimal" },
      body: JSON.stringify({ language }),
    });
  }

  async ensureAccount(userId: number): Promise<void> {
    await this.getOrCreateLanguage(userId);
    const query = new URLSearchParams({ on_conflict: "telegram_user_id" });
    await this.#request(`fortunis8_accounts?${query}`, {
      method: "POST",
      headers: { Prefer: "resolution=ignore-duplicates,return=minimal" },
      body: JSON.stringify({ telegram_user_id: userId }),
    });
  }

  async account(userId: number): Promise<JsonRecord> {
    await this.ensureAccount(userId);
    const query = new URLSearchParams({
      select:
        "diamonds,level,streak_count,selected_persona,premium_reading_credits",
      telegram_user_id: `eq.${userId}`,
      limit: "1",
    });
    const rows = await this.#request(`fortunis8_accounts?${query}`) as Array<
      JsonRecord
    >;
    if (!Array.isArray(rows) || !rows[0]) throw new StoreError();
    return rows[0];
  }

  async saveReading(
    userId: number,
    readingType: string,
    title: string,
    content: string,
    metadata: JsonRecord = {},
  ): Promise<void> {
    await this.ensureAccount(userId);
    await this.#request("fortunis8_readings", {
      method: "POST",
      headers: { Prefer: "return=minimal" },
      body: JSON.stringify({
        telegram_user_id: userId,
        reading_type: readingType,
        title: title.slice(0, 120),
        content: content.slice(0, 3500),
        metadata,
      }),
    });
  }

  async lastReading(userId: number): Promise<JsonRecord | null> {
    const query = new URLSearchParams({
      select: "reading_type,title,content,created_at",
      telegram_user_id: `eq.${userId}`,
      order: "created_at.desc",
      limit: "1",
    });
    const rows = await this.#request(`fortunis8_readings?${query}`) as Array<
      JsonRecord
    >;
    if (!Array.isArray(rows)) throw new StoreError();
    return rows[0] ?? null;
  }

  async claimDaily(userId: number): Promise<JsonRecord> {
    const result = await this.#rpc("fortunis8_claim_daily", {
      p_telegram_user_id: userId,
    });
    if (!result || typeof result !== "object" || Array.isArray(result)) {
      throw new StoreError();
    }
    return result as JsonRecord;
  }

  async claimQuest(userId: number, key: string): Promise<JsonRecord> {
    const result = await this.#rpc("fortunis8_claim_charity_quest", {
      p_telegram_user_id: userId,
      p_quest_key: key,
    });
    if (!result || typeof result !== "object" || Array.isArray(result)) {
      throw new StoreError();
    }
    return result as JsonRecord;
  }

  async setPersona(userId: number, persona: Persona): Promise<void> {
    await this.ensureAccount(userId);
    const query = new URLSearchParams({ telegram_user_id: `eq.${userId}` });
    await this.#request(`fortunis8_accounts?${query}`, {
      method: "PATCH",
      headers: { Prefer: "return=minimal" },
      body: JSON.stringify({ selected_persona: persona }),
    });
  }

  async createGame(
    userId: number,
    sessionId: string,
    difficulty: "easy" | "hard",
    prompt: string,
    options: string[],
    answer: string,
    reward: number,
  ): Promise<void> {
    await this.ensureAccount(userId);
    await this.#request("fortunis8_game_sessions", {
      method: "POST",
      headers: { Prefer: "return=minimal" },
      body: JSON.stringify({
        id: sessionId,
        telegram_user_id: userId,
        game_key: "arithmetic",
        difficulty,
        prompt: prompt.slice(0, 300),
        options: options.slice(0, 6),
        correct_answer: answer.slice(0, 50),
        reward_diamonds: reward,
        expires_at: new Date(Date.now() + 5 * 60_000).toISOString(),
      }),
    });
  }

  async completeGame(
    userId: number,
    sessionId: string,
    answer: string,
  ): Promise<JsonRecord> {
    const result = await this.#rpc("fortunis8_complete_game", {
      p_session_id: sessionId,
      p_telegram_user_id: userId,
      p_answer: answer.slice(0, 50),
    });
    if (!result || typeof result !== "object" || Array.isArray(result)) {
      throw new StoreError();
    }
    return result as JsonRecord;
  }

  async leaderboard(
    userId: number,
  ): Promise<{ scores: number[]; rank: number | null }> {
    const query = new URLSearchParams({
      select: "diamonds",
      order: "diamonds.desc",
      limit: "10",
    });
    const rows = await this.#request(`fortunis8_accounts?${query}`) as Array<
      JsonRecord
    >;
    if (!Array.isArray(rows)) throw new StoreError();
    const rank = await this.#rpc("fortunis8_get_rank", {
      p_telegram_user_id: userId,
    });
    return {
      scores: rows.map((row) => row.diamonds).filter((value): value is number =>
        Number.isSafeInteger(value) && (value as number) >= 0
      ),
      rank: Number.isSafeInteger(rank) ? rank as number : null,
    };
  }

  async createInvoice(
    userId: number,
    focus: Focus,
    amount: number,
    payload: string,
  ): Promise<void> {
    await this.ensureAccount(userId);
    await this.#request("fortunis8_pending_invoices", {
      method: "POST",
      headers: { Prefer: "return=minimal" },
      body: JSON.stringify({
        invoice_payload: payload,
        telegram_user_id: userId,
        product: "premium_palm_reading",
        focus,
        amount_stars: amount,
        currency: "XTR",
      }),
    });
  }

  async cancelInvoice(userId: number, payload: string): Promise<void> {
    const query = new URLSearchParams({
      invoice_payload: `eq.${payload}`,
      telegram_user_id: `eq.${userId}`,
    });
    await this.#request(`fortunis8_pending_invoices?${query}`, {
      method: "DELETE",
      headers: { Prefer: "return=minimal" },
    });
  }

  async validInvoice(
    payload: string,
    userId: number,
  ): Promise<JsonRecord | null> {
    const query = new URLSearchParams({
      select: "amount_stars,currency,telegram_user_id,expires_at",
      invoice_payload: `eq.${payload}`,
      telegram_user_id: `eq.${userId}`,
      limit: "1",
    });
    const rows = await this.#request(
      `fortunis8_pending_invoices?${query}`,
    ) as Array<JsonRecord>;
    if (!Array.isArray(rows) || !rows[0]) return null;
    const invoice = rows[0];
    const expires = typeof invoice.expires_at === "string"
      ? Date.parse(invoice.expires_at)
      : NaN;
    if (!Number.isFinite(expires) || expires <= Date.now()) return null;
    return invoice;
  }

  async recordPayment(
    userId: number,
    payload: string,
    chargeId: string,
    amount: number,
    currency: string,
  ): Promise<JsonRecord> {
    const result = await this.#rpc("fortunis8_record_star_payment", {
      p_telegram_user_id: userId,
      p_invoice_payload: payload,
      p_charge_id: chargeId,
      p_amount: amount,
      p_currency: currency,
    });
    if (!result || typeof result !== "object" || Array.isArray(result)) {
      throw new StoreError();
    }
    return result as JsonRecord;
  }

  async redeemPremium(
    userId: number,
    updateId: number,
    focus: Focus,
    title: string,
    content: string,
  ): Promise<JsonRecord> {
    const result = await this.#rpc(
      "fortunis8_redeem_premium_reading_for_update",
      {
        p_telegram_user_id: userId,
        p_telegram_update_id: updateId,
        p_focus: focus,
        p_title: title.slice(0, 120),
        p_content: content.slice(0, 3500),
      },
    );
    if (!result || typeof result !== "object" || Array.isArray(result)) {
      throw new StoreError();
    }
    return result as JsonRecord;
  }
}

export function getFunctionSecrets(env: (name: string) => string | undefined) {
  return requiredSecrets(env);
}
