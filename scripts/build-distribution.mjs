import { readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root=join(dirname(fileURLToPath(import.meta.url)),"..");
const sources=[
  "問題セット_第1問特集①-⑨.json",
  "問題セット_2025年度2級直前模試_第1回-第6回.json",
  "問題セット_2025年度3級直前模試_第1回-第4回.json"
];
const sets=[];
for(const name of sources)sets.push(JSON.parse(await readFile(join(root,"src",name),"utf8")));

let html=await readFile(join(root,"src","仕訳学習アプリ.html"),"utf8");
if(!html.includes("const BUNDLED_SETS=[];"))throw new Error("BUNDLED_SETS placeholder was not found");
html=html.replace("const BUNDLED_SETS=[];",`const BUNDLED_SETS=${JSON.stringify(sets)};`)
  .replace(/<span class="ver">(v[^<]+)<\/span>/,'<span class="ver">$1配布版</span>')
  .replaceAll('href="../manifest.webmanifest"','href="manifest.webmanifest"')
  .replaceAll('href="../assets/','href="assets/')
  .replaceAll('src="../assets/','src="assets/')
  .replace('navigator.serviceWorker.register("../sw.js")','navigator.serviceWorker.register("sw.js")');

await writeFile(join(root,"index.html"),html);
console.log(`Built index.html with ${sets.reduce((sum,set)=>sum+(set.questions||[]).length,0)} questions.`);
