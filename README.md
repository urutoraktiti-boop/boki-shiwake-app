# 日商簿記2級 仕訳トレーニングアプリ

大学生向けの日商簿記2級・仕訳問題反復学習アプリです。学生用アプリはGitHub Pagesで公開し、学習記録はブラウザ内保存とFirebaseへ保存します。学生は大学専用URLから学籍番号・学校コード付きアプリID・6桁暗証番号を登録し、端末やブラウザが変わっても同じ記録とアプリIDを復元できます。ランキングには学籍番号ではなくアプリIDを表示します。管理者はFirebase Authenticationでログインし、大学別・学籍番号別の成績確認、問題の公開対象・公開期間の設定ができます。

## 公開URL

- 学生用アプリ: https://urutoraktiti-boop.github.io/boki-shiwake-app/
- 管理者ダッシュボード: https://urutoraktiti-boop.github.io/boki-shiwake-app/admin/
- 学生向けデータ引き継ぎガイド: https://urutoraktiti-boop.github.io/boki-shiwake-app/help/

## 主なファイル

| ファイル | 役割 |
|---|---|
| `index.html` | 学生に配布する公開版（Study Journal UI）。従来49問＋2級模試48問＋3級模試60問（計157問）を同梱。模試108問は管理者が公開するまで非表示 |
| `src/仕訳学習アプリ.html` | 開発マスター版。編集は基本的にこちらへ行う |
| `src/問題セット_第1問特集①-⑨.json` | 問題データ原本 |
| `src/問題セット_2025年度2級直前模試_第1回-第6回.json` | 第1回〜第6回から指定8問ずつ取り込んだ公開用問題データ（48問） |
| `src/問題セット_2025年度3級直前模試_第1回-第4回.json` | 第1回〜第4回の第1問15問をすべて取り込んだ公開用問題データ（60問） |
| `skills/extract-boki-mock-pdf/` | 2025年度2級直前模試PDFから指定8問を、文字解説＋必要な図解画像の下書きJSONにするCodexスキル |
| `skills/extract-boki-mock-pdf/references/title-map.json` | 6回48問の問題タイトル（`topic`）を固定する対応表 |
| `drafts/2025-mock/` | 模試の確認済み下書きJSONと、6回48問を監査した図解画像索引 |
| `assets/explanations/2025-mock/` | 解説に必要な部分だけを切り出した確認済みPNG（PDF全ページは置かない） |
| `admin/index.html` | Study Journalデザインの管理者用成績ダッシュボード |
| `admin/invite.html` | 管理者招待後の確認ページ |
| `assets/identity-core.js` | 学籍番号の正規化、学生キー・暗証番号ハッシュ、履歴統合の共通処理 |
| `manifest.webmanifest` / `sw.js` | ホーム画面追加（PWA）と最新版優先キャッシュ |
| `scripts/build-distribution.mjs` | マスター版と3つの問題JSONから配布版 `index.html` を再生成するスクリプト |
| `firestore.rules` | Firestoreセキュリティルール |
| `引き継ぎ書.md` | 詳細な仕様・運用メモ・次回開発者向けの引き継ぎ |

## 更新時の注意

- 学生用アプリの改修は、まず `src/仕訳学習アプリ.html` を編集します。
- 配布版を更新するときは、リポジトリ直下で `node scripts/build-distribution.mjs` を実行します。マスター版の `BUNDLED_SETS` に3つの問題JSONを注入し、パスと版数を配布版用に直した `index.html` が生成されます。
- 2025年度2級直前模試PDFを取り込むときは `skills/extract-boki-mock-pdf/` を使います。問題・解答・解説を照合し、文字だけでは分かりにくい図解だけをPNGで添えた下書きJSONまでを作ります。自動公開はしません。
- 2025年度3級直前模試は、各回の第1問1〜15を問題・解答・解説の対象ページで画像と文字を照合し、固定ID・根拠ページ付きで取り込みます。
- 管理者が学生画面を確認するときは、管理者ダッシュボードの「確認用に開く」を使います。このURLには `preview=admin` が付き、初回登録ポップアップを出しません。
- 学籍番号による復元、重複統合、学生ごとの利用停止を使うには、最新版の `firestore.rules` をFirebaseへ公開する必要があります。本番更新は「ルール公開 → 学生アプリ・管理画面公開 → 管理画面で統合候補を確認 → 一括移行」の順で行います。
- アプリIDは学生入力部分を全角カタカナ＋数字2〜12文字に正規化し、大学専用URLに対応する学校コード（例：`GA-`）を自動付与します。学生記録の本人識別には引き続き `studentKey` を使います。
- 旧同期コードの記録は一括移行後も削除せず、`migratedTo` が付いた読み取り専用記録として残します。通常の学生一覧・集計には新しい学生記録だけを表示します。
- 管理者ダッシュボードやFirestoreルールを変更した場合は、`引き継ぎ書.md` もあわせて更新してください。
- GitHub Pagesの公開反映には数分かかる場合があります。Actions / Pages のデプロイジョブが queued の間は、公開URLが古い画面を返すことがあります。
