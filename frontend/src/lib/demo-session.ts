const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://127.0.0.1:8000";

const TOKEN_KEY =
  "stayops:demoSessionToken";

let createSessionPromise:
  Promise<string> | null = null;

type DemoSessionCreateResponse = {
  session_id: string;
  session_token: string;
  expires_at: string;
  ttl_hours: number;
};

function getStoredToken() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(
    TOKEN_KEY
  );
}

function storeToken(token: string) {
  window.localStorage.setItem(
    TOKEN_KEY,
    token
  );
}

export function clearDemoSession() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(
    TOKEN_KEY
  );
  window.localStorage.removeItem(
    "stayops:selectedBookingId"
  );
}

async function createDemoSession(): Promise<string> {
  const response = await fetch(
    `${API_URL}/demo/sessions`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    throw new Error(
      `Demo session request failed: ${response.status}`
    );
  }

  const data:
    DemoSessionCreateResponse =
      await response.json();

  storeToken(
    data.session_token
  );

  return data.session_token;
}

export async function ensureDemoSession(): Promise<string> {
  const existingToken =
    getStoredToken();

  if (existingToken) {
    return existingToken;
  }

  if (!createSessionPromise) {
    createSessionPromise =
      createDemoSession();
  }

  try {
    return await createSessionPromise;
  } finally {
    createSessionPromise = null;
  }
}

async function fetchWithToken(
  input: string | URL,
  init: RequestInit,
  token: string,
) {
  const headers =
    new Headers(init.headers);

  headers.set(
    "X-StayOps-Demo-Token",
    token
  );

  return fetch(
    input,
    {
      ...init,
      headers,
    }
  );
}

export async function demoFetch(
  input: string | URL,
  init: RequestInit = {},
) {
  let token =
    await ensureDemoSession();

  let response =
    await fetchWithToken(
      input,
      init,
      token,
    );

  if (response.status !== 401) {
    return response;
  }

  clearDemoSession();

  token =
    await ensureDemoSession();

  response =
    await fetchWithToken(
      input,
      init,
      token,
    );

  return response;
}
