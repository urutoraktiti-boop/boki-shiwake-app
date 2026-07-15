const test = require("node:test");
const assert = require("node:assert/strict");
const identity = require("../assets/identity-core.js");

const links = [{ code:"gakushuin", displayCode:"GA", name:"学習院大学" }];

test("studentIdentity normalizes full-width IDs and whitespace", async () => {
  const a = await identity.studentIdentity("学習院大学", " ab １２３ ", links);
  const b = await identity.studentIdentity("学習院大学", "AB123", links);
  assert.equal(a.studentKey, b.studentKey);
  assert.equal(a.sidNormalized, "AB123");
});

test("PIN verifiers accept only the original six digits", async () => {
  const verifier = await identity.createPinVerifier("123456");
  const another = await identity.createPinVerifier("123456");
  assert.match(verifier.salt, /^[0-9a-f]{32}$/);
  assert.match(verifier.hash, /^[0-9a-f]{64}$/);
  assert.notEqual(verifier.salt, another.salt);
  assert.notEqual(verifier.hash, another.hash);
  assert.equal(await identity.verifyPin("123456", verifier), true);
  assert.equal(await identity.verifyPin("654321", verifier), false);
});

test("app IDs normalize half-width katakana and full-width digits", () => {
  assert.equal(identity.normalizeAppId(" ｺﾂｻｸ０１ "), "コツサク01");
  assert.equal(identity.isValidAppId("コツサク01"), true);
  assert.equal(identity.isValidAppId("こつさく01"), false);
  assert.equal(identity.isValidAppId("コツ・サク"), false);
  assert.equal(identity.isValidAppId("ア"), false);
});

test("display IDs prepend the university code and reject student-number reuse", () => {
  assert.equal(identity.universityDisplayCode("学習院大学", links), "GA");
  assert.equal(identity.formatDisplayId("学習院大学", "コツサク01", links), "GA-コツサク01");
  assert.equal(identity.formatDisplayId("未登録大学", "ネコ7", links), "OT-ネコ7");
  assert.equal(identity.appIdValidationMessage("123456", "１２３４５６"), "アプリIDには学籍番号と異なる文字を設定してください。");
});

test("assignment achievements use completion and the highest score tier", () => {
  assert.deepEqual(identity.assignmentAchievement([]), {
    completed:false, key:"", label:"", rate:0, score:0, max:0, attempts:0
  });
  assert.equal(identity.assignmentAchievement([{score:79,max:100}]).key, "complete");
  assert.equal(identity.assignmentAchievement([{score:80,max:100}]).label, "よくできました");
  assert.equal(identity.assignmentAchievement([{score:90,max:100}]).label, "大変よくできました");
  assert.equal(identity.assignmentAchievement([{score:10,max:10}]).label, "素晴らしい！");
  const retained = identity.assignmentAchievement([{score:10,max:10},{score:6,max:10}]);
  assert.equal(retained.key, "perfect");
  assert.equal(retained.attempts, 2);
});

test("mergeStores keeps distinct IDs and deduplicates copied legacy events", () => {
  const legacy = { qid:"q1", correct:true, date:"2026-07-15", ms:1000 };
  const a = { history:[legacy, { id:"h-1", qid:"q2" }], tests:[], updatedAt:1, profile:{univ:"A",sid:"1"} };
  const b = { history:[legacy, { id:"h-2", qid:"q3" }], tests:[], updatedAt:2, profile:{univ:"A",sid:"1",group:"2"} };
  const merged = identity.mergeStores(a, b);
  assert.equal(merged.history.length, 3);
  assert.equal(merged.profile.group, "2");
});

test("mergeStores preserves repeated attempts from one legacy record", () => {
  const legacy = { qid:"q1", correct:false, date:"2026-07-15", ms:500 };
  const merged = identity.mergeStores({ history:[legacy, legacy] }, { history:[legacy] });
  assert.equal(merged.history.length, 2);
});

test("mergeStores keeps the newer profile regardless of argument order", () => {
  const newer = { updatedAt:20, profile:{univ:"A",sid:"1",group:"new"}, meta:{theme:"new"} };
  const older = { updatedAt:10, profile:{univ:"A",sid:"1",group:"old"}, meta:{theme:"old",legacy:true} };
  const merged = identity.mergeStores(newer, older);
  assert.equal(merged.profile.group, "new");
  assert.equal(merged.meta.theme, "new");
  assert.equal(merged.meta.legacy, true);
  assert.equal(merged.updatedAt, 20);
});

test("mergeStores orders merged answer events chronologically", () => {
  const newer = { id:"new", qid:"q1", answeredAt:"2026-07-15T10:00:00.000Z", correct:true };
  const older = { id:"old", qid:"q1", answeredAt:"2026-07-15T09:00:00.000Z", correct:false };
  const merged = identity.mergeStores({ history:[newer] }, { history:[older] });
  assert.deepEqual(merged.history.map(x => x.id), ["old", "new"]);
});
