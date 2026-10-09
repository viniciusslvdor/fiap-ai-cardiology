/**
 * SIMULATED authentication for academic purposes.
 *
 * - There is no backend: the demo credentials live in the front-end itself.
 * - The "JWT" is fake: it has the header.payload.signature format, but the signature is not
 *   cryptographic and anyone can edit the token in localStorage.
 * - DO NOT use this pattern in a real system.
 */

export const DEMO_CREDENTIALS = {
  email: 'admin@cardioia.com',
  password: 'cardioia123',
};

const DEMO_USER = {
  id: 1,
  name: 'Admin CardioIA',
  email: DEMO_CREDENTIALS.email,
  role: 'Medical team (demo)',
};

const FAKE_SIGNATURE = 'fake-jwt-signature-cardioia';
const SESSION_HOURS = 8;

const toBase64 = (obj) => btoa(JSON.stringify(obj));
const fromBase64 = (str) => JSON.parse(atob(str));
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/** Builds a token that "looks like" a JWT: header.payload.fake-signature */
function createFakeJwt(user) {
  const header = { alg: 'none', typ: 'JWT' };
  const now = Math.floor(Date.now() / 1000);
  const payload = { sub: user.id, name: user.name, email: user.email, iat: now, exp: now + SESSION_HOURS * 3600 };
  return `${toBase64(header)}.${toBase64(payload)}.${FAKE_SIGNATURE}`;
}

/** Reads the payload of the fake token. Returns null if the format is invalid. */
export function decodeFakeJwt(token) {
  try {
    const [, payload, signature] = token.split('.');
    if (signature !== FAKE_SIGNATURE) return null;
    return fromBase64(payload);
  } catch {
    return null;
  }
}

/** Checks only format and expiration (there is no cryptographic verification). */
export function isTokenValid(token) {
  const payload = token ? decodeFakeJwt(token) : null;
  return Boolean(payload && payload.exp * 1000 > Date.now());
}

/** Simulates a POST /login call with network delay. */
export async function login(email, password) {
  await wait(600);
  const emailOk = email.trim().toLowerCase() === DEMO_CREDENTIALS.email;
  if (!emailOk || password !== DEMO_CREDENTIALS.password) {
    throw new Error('Invalid email or password. Use the demo credentials.');
  }
  return { token: createFakeJwt(DEMO_USER), user: DEMO_USER };
}
