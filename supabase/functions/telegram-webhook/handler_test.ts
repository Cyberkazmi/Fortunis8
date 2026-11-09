import { createWebhookHandler, type HandlerDependencies } from "./handler.ts";
import type { Fetcher } from "./store.ts";

const SECRET = "A_valid-webhook-secret_123456789";
const ENV: Record<string, string> = {
  SUPABASE_URL: "https://fortunis8-test.supabase.co",
  SUPABASE_SERVICE_ROLE_KEY: "test-service-key-not-real",
  TELEGRAM_BOT_TOKEN: "123456:test-bot-token-not-real",
  TELEGRAM_WEBHOOK_SECRET: SECRET,
  PREMIUM_PALM_PRICE_STARS: "25",
};

type CapturedRequest = {
  url: string;
  method: string;
  body: Record<string, unknown> | null;
};

function setup(options: {
  rpc?: Record<string, unknown>;
  invoiceRows?: Record<string, unknown>[];
  languageRows?: Record<string, unknown>[];
  accountRows?: Record<string, unknown>[];
} = {}) {
  const captured: CapturedRequest[] = [];
  const rpcCallCounts = new Map<string, number>();
  // deno-lint-ignore require-await
  const fetcher: Fetcher = async (input, init = {}) => {
    const url = new URL(String(input));
    let body: Record<string, unknown> | null = null;
    if (typeof init.body === "string") {
      try {
        body = JSON.parse(init.body) as Record<string, unknown>;
      } catch {
        body = null;
      }
    }
    captured.push({
      url: `${url.origin}${url.pathname}${url.search}`,
      method: init.method ?? "GET",
      body,
    });
    if (url.hostname === "api.telegram.org") {
      return Response.json({ ok: true, result: true });
    }
    const path = url.pathname;
    if (path.endsWith("/fortunis8_users") && (init.method ?? "GET") === "GET") {
      return Response.json(options.languageRows ?? [{ language: "en" }]);
    }
    if (
      path.endsWith("/fortunis8_accounts") && (init.method ?? "GET") === "GET"
    ) {
      return Response.json(
        options.accountRows ??
          [{
            diamonds: 12,
            level: 1,
            streak_count: 2,
            selected_persona: "Wizard",
            premium_reading_credits: 1,
          }],
      );
    }
    if (
      path.endsWith("/fortunis8_pending_invoices") &&
      (init.method ?? "GET") === "GET"
    ) {
      return Response.json(
        options.invoiceRows ??
          [{
            amount_stars: 25,
            currency: "XTR",
            telegram_user_id: 44,
            expires_at: new Date(Date.now() + 60_000).toISOString(),
          }],
      );
    }
    if (path.includes("/rpc/")) {
      const rpcName = path.split("/rpc/")[1];
      const configured = options.rpc?.[rpcName];
      const callIndex = rpcCallCounts.get(rpcName) ?? 0;
      rpcCallCounts.set(rpcName, callIndex + 1);
      const result = Array.isArray(configured)
        ? configured[callIndex] ?? configured.at(-1)
        : configured ??
          (rpcName === "fortunis8_get_rank"
            ? 1
            : { ok: true, claimed: true, reward: 2, streak: 2, diamonds: 14 });
      return Response.json(result);
    }
    return new Response("[]", {
      status: 201,
      headers: { "content-type": "application/json" },
    });
  };
  const deps: HandlerDependencies = { env: (name) => ENV[name], fetcher };
  const handler = createWebhookHandler(deps);
  const post = (update: unknown, secret = SECRET) =>
    new Request("https://function.test/telegram-webhook", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "X-Telegram-Bot-Api-Secret-Token": secret,
      },
      body: JSON.stringify(update),
    });
  return { handler, captured, post };
}

function messageUpdate(text: string, updateId = 100) {
  return {
    update_id: updateId,
    message: {
      message_id: 1,
      chat: { id: 44, type: "private" },
      from: { id: 44 },
      text,
    },
  };
}

Deno.test("rejects non-POST requests before processing", async () => {
  const { handler, captured } = setup();
  const response = await handler(
    new Request("https://function.test/", { method: "GET" }),
  );
  if (response.status !== 405) {
    throw new Error(`expected 405, got ${response.status}`);
  }
  if (captured.length) {
    throw new Error("GET request unexpectedly called a provider");
  }
});

Deno.test("rejects a missing or incorrect Telegram webhook secret", async () => {
  const { handler, captured, post } = setup();
  const response = await handler(post(messageUpdate("/start"), "wrong-secret"));
  if (response.status !== 401) {
    throw new Error(`expected 401, got ${response.status}`);
  }
  if (captured.length) {
    throw new Error("unauthenticated request unexpectedly reached a provider");
  }
});

Deno.test("fails closed when a required function secret is absent", async () => {
  const { captured } = setup();
  const handler = createWebhookHandler({
    env: () => undefined,
    fetcher: () => Promise.reject(new Error("must not call")),
  });
  const response = await handler(
    new Request("https://function.test/", {
      method: "POST",
      headers: { "X-Telegram-Bot-Api-Secret-Token": SECRET },
      body: "{}",
    }),
  );
  if (response.status !== 503) {
    throw new Error(`expected 503, got ${response.status}`);
  }
  if (captured.length) {
    throw new Error("provider called despite missing secrets");
  }
});

Deno.test("/start creates/loads the private account and sends language and menu keyboards", async () => {
  const { handler, captured, post } = setup();
  const response = await handler(post(messageUpdate("/start")));
  if (response.status !== 200) {
    throw new Error(`expected 200, got ${response.status}`);
  }
  const sends = captured.filter((request) =>
    request.url.includes("api.telegram.org") &&
    request.url.endsWith("/sendMessage")
  );
  if (sends.length !== 2) {
    throw new Error(`expected two onboarding messages, got ${sends.length}`);
  }
  const serialized = JSON.stringify(sends);
  if (!serialized.includes("lang:ur") || !serialized.includes("f8:fortune")) {
    throw new Error("expected language and feature keyboards");
  }
});

Deno.test("daily reward uses the existing idempotent Fortunis8 RPC", async () => {
  const { handler, captured, post } = setup({
    rpc: {
      fortunis8_claim_daily: {
        ok: true,
        claimed: true,
        reward: 3,
        streak: 2,
        diamonds: 15,
      },
    },
  });
  const response = await handler(post(messageUpdate("/daily")));
  if (response.status !== 200) {
    throw new Error(`expected 200, got ${response.status}`);
  }
  const rpc = captured.find((request) =>
    request.url.includes("/rpc/fortunis8_claim_daily")
  );
  if (!rpc) throw new Error("daily claim did not use the database RPC");
  const outbound = captured.find((request) =>
    request.url.includes("/sendMessage")
  );
  if (!JSON.stringify(outbound?.body).includes("+3 diamonds")) {
    throw new Error("daily reply missing reward details");
  }
});

Deno.test("horoscope input stays out of persisted reading body and metadata", async () => {
  const { handler, captured, post } = setup();
  const response = await handler(
    post(messageUpdate("/horoscope 1995-08-20 09:30, Lahore")),
  );
  if (response.status !== 200) {
    throw new Error(`expected 200, got ${response.status}`);
  }
  const saved = captured.find((request) =>
    request.url.endsWith("/fortunis8_readings") && request.method === "POST"
  );
  if (!saved?.body) throw new Error("reading was not persisted");
  const persisted = JSON.stringify(saved.body);
  for (const privateInput of ["1995-08-20", "09:30", "Lahore"]) {
    if (persisted.includes(privateInput)) {
      throw new Error(`horoscope input persisted: ${privateInput}`);
    }
  }
  if (!persisted.includes("sun_sign")) {
    throw new Error("sun sign metadata missing");
  }
});

Deno.test("replayed Stars payment does not redeem another credit", async () => {
  const { handler, captured, post } = setup({
    rpc: {
      fortunis8_record_star_payment: {
        ok: true,
        credited: false,
        duplicate: true,
      },
    },
  });
  const update = {
    update_id: 102,
    message: {
      message_id: 3,
      chat: { id: 44, type: "private" },
      from: { id: 44 },
      successful_payment: {
        invoice_payload: "fortunis8:44:random-payload",
        telegram_payment_charge_id: "charge-1",
        total_amount: 25,
        currency: "XTR",
      },
    },
  };
  const response = await handler(post(update));
  if (response.status !== 200) {
    throw new Error(`expected 200, got ${response.status}`);
  }
  if (
    captured.some((request) =>
      request.url.includes("/rpc/fortunis8_redeem_premium_reading")
    )
  ) {
    throw new Error(
      "duplicate payment must not consume a second premium credit",
    );
  }
  const rpc = captured.find((request) =>
    request.url.includes("/rpc/fortunis8_record_star_payment")
  );
  if (!rpc) {
    throw new Error("payment was not validated through the existing RPC");
  }
});

Deno.test("pre-checkout rejects an amount mismatch before payment can complete", async () => {
  const { handler, captured, post } = setup();
  const update = {
    update_id: 103,
    pre_checkout_query: {
      id: "pre-checkout-id",
      from: { id: 44 },
      invoice_payload: "fortunis8:44:payload",
      total_amount: 99,
      currency: "XTR",
    },
  };
  const response = await handler(post(update));
  if (response.status !== 200) {
    throw new Error(`expected 200, got ${response.status}`);
  }
  const answer = captured.find((request) =>
    request.url.includes("/answerPreCheckoutQuery")
  );
  if (answer?.body?.ok !== false) {
    throw new Error("mismatched amount was not rejected");
  }
});

Deno.test("group commands are not handled as private feature actions", async () => {
  const { handler, captured, post } = setup();
  const update = {
    update_id: 104,
    message: {
      message_id: 1,
      chat: { id: -44, type: "group" },
      from: { id: 44 },
      text: "/fortune",
    },
  };
  const response = await handler(post(update));
  if (response.status !== 200) {
    throw new Error(`expected 200, got ${response.status}`);
  }
  if (
    captured.some((request) =>
      request.url.includes("/rest/v1/fortunis8_readings")
    )
  ) throw new Error("group reading was persisted");
});

Deno.test("JWT bypass is scoped to the Telegram webhook only", async () => {
  const config = await Deno.readTextFile(
    new URL("../../config.toml", import.meta.url),
  );
  const sections = [...config.matchAll(/^\[functions\.([^\]]+)\]/gm)].map((
    match,
  ) => match[1]);
  if (sections.length !== 1 || sections[0] !== "telegram-webhook") {
    throw new Error(
      `unexpected function JWT config sections: ${sections.join(",")}`,
    );
  }
  const section = config.split("[functions.telegram-webhook]")[1] ?? "";
  if (!/^\s*verify_jwt\s*=\s*false\s*$/m.test(section)) {
    throw new Error("webhook JWT bypass is not explicit");
  }
});
Deno.test("premium redemption replay reuses the same update_id and result", async () => {
  const { handler, captured, post } = setup({
    rpc: {
      fortunis8_redeem_premium_reading_for_update: [
        {
          ok: true,
          duplicate: false,
          reading_id: "reading-1",
          credits_remaining: 0,
        },
        {
          ok: true,
          duplicate: true,
          reading_id: "reading-1",
          credits_remaining: 0,
        },
      ],
    },
  });
  const update = {
    update_id: 105,
    callback_query: {
      id: "callback-1",
      from: { id: 44 },
      message: { message_id: 1, chat: { id: 44, type: "private" } },
      data: "palm:focus:use:work",
    },
  };
  const first = await handler(post(update));
  const replay = await handler(post(update));
  if (first.status !== 200 || replay.status !== 200) {
    throw new Error("both original and replay should be acknowledged");
  }
  const redemptions = captured.filter((request) =>
    request.url.includes("/rpc/fortunis8_redeem_premium_reading_for_update")
  );
  if (redemptions.length !== 2) {
    throw new Error(
      `expected two RPC calls for two deliveries, got ${redemptions.length}`,
    );
  }
  if (
    redemptions.some((request) => request.body?.p_telegram_update_id !== 105)
  ) {
    throw new Error("redemption RPC did not receive the Telegram update_id");
  }
  const replayMessage = captured.filter((request) =>
    request.url.includes("/sendMessage")
  ).at(-1);
  if (!JSON.stringify(replayMessage?.body).includes("already processed")) {
    throw new Error("replay did not return the saved duplicate result message");
  }
});

Deno.test("malformed update variants are safely rejected or acknowledged", async () => {
  const { handler, captured, post } = setup();
  const missingId = await handler(post({
    message: {
      chat: { id: 44, type: "private" },
      from: { id: 44 },
      text: "/start",
    },
  }));
  if (missingId.status !== 400) {
    throw new Error(
      `expected 400 for a missing update_id, got ${missingId.status}`,
    );
  }
  const malformedCheckout = await handler(post({
    update_id: 106,
    pre_checkout_query: { id: "pre-checkout-malformed" },
  }));
  const malformedCallback = await handler(post({
    update_id: 107,
    callback_query: { id: "callback-malformed" },
  }));
  if (malformedCheckout.status !== 200 || malformedCallback.status !== 200) {
    throw new Error(
      "malformed supported updates should be acknowledged safely",
    );
  }
  const checkoutAnswer = captured.find((request) =>
    request.url.includes("/answerPreCheckoutQuery")
  );
  const callbackAnswer = captured.find((request) =>
    request.url.includes("/answerCallbackQuery")
  );
  if (checkoutAnswer?.body?.ok !== false || !callbackAnswer) {
    throw new Error("malformed callback or checkout spinner was not settled");
  }
  if (captured.some((request) => request.url.includes("/rest/v1/"))) {
    throw new Error("malformed update unexpectedly accessed the database");
  }
});
