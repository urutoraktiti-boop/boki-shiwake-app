(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.BokiIdentity = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const SCHEMA_VERSION = 2;
  const PIN_ITERATIONS = 120000;
  const APP_ID_MIN_LENGTH = 2;
  const APP_ID_MAX_LENGTH = 12;

  function normalizeStudentId(value) {
    return String(value ?? "").normalize("NFKC").trim().replace(/\s+/g, "").toUpperCase();
  }

  function normalizeUniversity(value) {
    return String(value ?? "").normalize("NFKC").trim().replace(/\s+/g, " ");
  }

  function universityCode(university, links) {
    const normalized = normalizeUniversity(university);
    const hit = (Array.isArray(links) ? links : []).find(item => normalizeUniversity(item && item.name) === normalized);
    return hit ? String(hit.code) : `other:${normalized.toUpperCase()}`;
  }

  function universityDisplayCode(university, links) {
    const normalized = normalizeUniversity(university);
    const hit = (Array.isArray(links) ? links : []).find(item => normalizeUniversity(item && item.name) === normalized);
    const code = String(hit && (hit.displayCode || hit.schoolCode) || "OT").normalize("NFKC").toUpperCase().replace(/[^A-Z0-9]/g, "");
    return code.slice(0, 4) || "OT";
  }

  function normalizeAppId(value) {
    return String(value ?? "").normalize("NFKC").trim();
  }

  function isValidAppId(value) {
    const normalized = normalizeAppId(value);
    const length = Array.from(normalized).length;
    return length >= APP_ID_MIN_LENGTH
      && length <= APP_ID_MAX_LENGTH
      && /^[ァ-ヺー0-9]+$/.test(normalized);
  }

  function appIdValidationMessage(value, sid) {
    const normalized = normalizeAppId(value);
    if (!isValidAppId(normalized)) return `アプリIDは全角カタカナと数字で、${APP_ID_MIN_LENGTH}～${APP_ID_MAX_LENGTH}文字以内にしてください。`;
    if (normalizeStudentId(normalized) === normalizeStudentId(sid)) return "アプリIDには学籍番号と異なる文字を設定してください。";
    return "";
  }

  function formatDisplayId(university, appId, links) {
    const normalized = normalizeAppId(appId);
    if (!isValidAppId(normalized)) return `${universityDisplayCode(university, links)}-ミセッテイ`;
    return `${universityDisplayCode(university, links)}-${normalized}`;
  }

  function bytesToHex(bytes) {
    return Array.from(bytes, byte => byte.toString(16).padStart(2, "0")).join("");
  }

  function hexToBytes(hex) {
    const clean = String(hex || "").replace(/[^0-9a-f]/gi, "");
    const out = new Uint8Array(Math.floor(clean.length / 2));
    for (let i = 0; i < out.length; i++) out[i] = parseInt(clean.slice(i * 2, i * 2 + 2), 16);
    return out;
  }

  function cryptoApi() {
    const value = typeof globalThis !== "undefined" ? globalThis.crypto : null;
    if (!value || !value.subtle) throw new Error("このブラウザでは安全な暗証番号処理を利用できません。");
    return value;
  }

  async function sha256Hex(value) {
    const bytes = new TextEncoder().encode(String(value));
    const digest = await cryptoApi().subtle.digest("SHA-256", bytes);
    return bytesToHex(new Uint8Array(digest));
  }

  async function studentIdentity(university, sid, links) {
    const univ = normalizeUniversity(university);
    const sidNormalized = normalizeStudentId(sid);
    if (!univ || !sidNormalized) throw new Error("大学名と学籍番号を入力してください。");
    const univCode = universityCode(univ, links);
    const digest = await sha256Hex(`boki2-student-v1|${univCode}|${sidNormalized}`);
    return {
      studentKey: `STU-${digest.slice(0, 40).toUpperCase()}`,
      univ,
      univCode,
      sid: String(sid ?? "").normalize("NFKC").trim(),
      sidNormalized
    };
  }

  function randomHex(length) {
    const bytes = new Uint8Array(Math.ceil(length / 2));
    cryptoApi().getRandomValues(bytes);
    return bytesToHex(bytes).slice(0, length);
  }

  async function derivePinHash(pin, salt, iterations) {
    if (!/^\d{6}$/.test(String(pin || ""))) throw new Error("暗証番号は数字6桁で入力してください。");
    const subtle = cryptoApi().subtle;
    const key = await subtle.importKey("raw", new TextEncoder().encode(String(pin)), "PBKDF2", false, ["deriveBits"]);
    const bits = await subtle.deriveBits({
      name: "PBKDF2",
      salt: hexToBytes(salt),
      iterations,
      hash: "SHA-256"
    }, key, 256);
    return bytesToHex(new Uint8Array(bits));
  }

  async function createPinVerifier(pin) {
    const salt = randomHex(32);
    return { salt, hash: await derivePinHash(pin, salt, PIN_ITERATIONS), iterations: PIN_ITERATIONS };
  }

  async function verifyPin(pin, verifier) {
    if (!verifier || !verifier.salt || !verifier.hash) return false;
    if (!/^\d{6}$/.test(String(pin || ""))) return false;
    const iterations = Number(verifier.iterations) || PIN_ITERATIONS;
    return (await derivePinHash(pin, verifier.salt, iterations)) === verifier.hash;
  }

  function newEventId(prefix) {
    if (cryptoApi().randomUUID) return `${prefix || "evt"}-${cryptoApi().randomUUID()}`;
    return `${prefix || "evt"}-${Date.now().toString(36)}-${randomHex(20)}`;
  }

  function clone(value) {
    return value == null ? value : JSON.parse(JSON.stringify(value));
  }

  function stableObject(value) {
    if (Array.isArray(value)) return value.map(stableObject);
    if (value && typeof value === "object") {
      const out = {};
      Object.keys(value).sort().forEach(key => { out[key] = stableObject(value[key]); });
      return out;
    }
    return value;
  }

  function legacyFingerprint(value) {
    const copy = clone(value) || {};
    delete copy.id;
    delete copy.attemptId;
    delete copy.answeredAt;
    delete copy.completedAt;
    return JSON.stringify(stableObject(copy));
  }

  /* ID付きは集合和、旧形式は同じ配列コピーを二重計上しないよう最大出現数で統合する。 */
  function mergeEventArrays(left, right) {
    const a = Array.isArray(left) ? clone(left) : [];
    const b = Array.isArray(right) ? clone(right) : [];
    const out = [];
    const ids = new Set();
    const legacyCounts = new Map();

    function addPrimary(item) {
      const id = item && (item.id || item.attemptId);
      if (id) {
        if (!ids.has(id)) { ids.add(id); out.push(item); }
        return;
      }
      const fp = legacyFingerprint(item);
      legacyCounts.set(fp, (legacyCounts.get(fp) || 0) + 1);
      out.push(item);
    }
    a.forEach(addPrimary);

    const seenRight = new Map();
    b.forEach(item => {
      const id = item && (item.id || item.attemptId);
      if (id) {
        if (!ids.has(id)) { ids.add(id); out.push(item); }
        return;
      }
      const fp = legacyFingerprint(item);
      const n = (seenRight.get(fp) || 0) + 1;
      seenRight.set(fp, n);
      if (n > (legacyCounts.get(fp) || 0)) out.push(item);
    });
    return out.map((item, index) => ({ item, index, time: Date.parse(item?.answeredAt || item?.completedAt || item?.date || "") || 0 }))
      .sort((x, y) => x.time - y.time || x.index - y.index)
      .map(entry => entry.item);
  }

  function mergeSets(left, right) {
    const byName = new Map();
    [...(Array.isArray(left) ? left : []), ...(Array.isArray(right) ? right : [])].forEach(set => {
      if (!set || !set.name) return;
      const current = byName.get(set.name);
      if (!current || (set.questions || []).length > (current.questions || []).length) byName.set(set.name, clone(set));
    });
    return [...byName.values()];
  }

  function mergeStores(left, right) {
    const a = left && typeof left === "object" ? clone(left) : {};
    const b = right && typeof right === "object" ? clone(right) : {};
    const aTime = Number(a.updatedAt || 0);
    const bTime = Number(b.updatedAt || 0);
    const newer = bTime >= aTime ? b : a;
    const older = bTime >= aTime ? a : b;
    return {
      history: mergeEventArrays(a.history, b.history),
      sets: mergeSets(a.sets, b.sets),
      meta: { ...(older.meta || {}), ...(newer.meta || {}) },
      tests: mergeEventArrays(a.tests, b.tests),
      profile: clone(newer.profile || a.profile || b.profile || null),
      updatedAt: Math.max(aTime, bTime) || Date.now(),
      schemaVersion: SCHEMA_VERSION
    };
  }

  return {
    SCHEMA_VERSION,
    PIN_ITERATIONS,
    APP_ID_MIN_LENGTH,
    APP_ID_MAX_LENGTH,
    normalizeStudentId,
    normalizeUniversity,
    universityCode,
    universityDisplayCode,
    normalizeAppId,
    isValidAppId,
    appIdValidationMessage,
    formatDisplayId,
    sha256Hex,
    studentIdentity,
    createPinVerifier,
    verifyPin,
    newEventId,
    mergeEventArrays,
    mergeStores
  };
});
