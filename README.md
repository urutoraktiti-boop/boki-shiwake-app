# 日商簿記2級 仕訳トレーニングアプリ

大学生向けの日商簿記2級・仕訳問題反復学習アプリです。学生用アプリはGitHub Pagesで公開し、学習記録はブラウザ内保存とFirebase同期コードで扱います。管理者はFirebase Authenticationでログインし、大学別・学籍番号別の成績確認、問題の公開対象・公開期間の設定ができます。

## 公開URL

- 学生用アプリ: https://urutoraktiti-boop.github.io/boki-shiwake-app/
- 管理者ダッシュボード: https://urutoraktiti-boop.github.io/boki-shiwake-app/admin/
- 学生向けデータ引き継ぎガイド: https://urutoraktiti-boop.github.io/boki-shiwake-app/help/

## 主なファイル

| ファイル | 役割 |
|---|---|
| `index.html` | 学生に配布する公開版（Study Journal UI）。従来49問＋模試48問（計97問）を同梱。模試48問は管理者が公開するまで非表示 |
| `src/仕訳学習アプリ.html` | 開発マスター版。編集は基本的にこちらへ行う |
| `src/問題セット_第1問特集①-⑨.json` | 問題データ原本 |
| `src/問題セット_2025年度2級直前模試_第1回-第6回.json` | 第1回〜第6回から指定8問ずつ取り込んだ公開用問題データ（48問） |
| `skills/extract-boki-mock-pdf/` | 2025年度2級直前模試PDFから指定8問を、文字解説＋必要な図解画像の下書きJSONにするCodexスキル |
| `skills/extract-boki-mock-pdf/references/title-map.json` | 6回48問の問題タイトル（`topic`）を固定する対応表 |
| `drafts/2025-mock/` | 模試の確認済み下書きJSONと、6回48問を監査した図解画像索引 |
| `assets/explanations/2025-mock/` | 解説に必要な部分だけを切り出した確認済みPNG（PDF全ページは置かない） |
| `admin/index.html` | Study Journalデザインの管理者用成績ダッシュボード |
| `admin/invite.html` | 管理者招待後の確認ページ |
| `firestore.rules` | Firestoreセキュリティルール |
| `引き継ぎ書.md` | 詳細な仕様・運用メモ・次回開発者向けの引き継ぎ |

## 更新時の注意

- 学生用アプリの改修は、まず `src/仕訳学習アプリ.html` を編集します。
- 配布版を更新するときは、マスター版の `BUNDLED_SETS` に2つの問題JSONを注入して `index.html` を再生成します。
- 2025年度2級直前模試PDFを取り込むときは `skills/extract-boki-mock-pdf/` を使います。問題・解答・解説を照合し、文字だけでは分かりにくい図解だけをPNGで添えた下書きJSONまでを作ります。自動公開はしません。
- 管理者が学生画面を確認するときは、管理者ダッシュボードの「確認用に開く」を使います。このURLには `preview=admin` が付き、初回登録ポップアップを出しません。
- 問題公開設定を使うには、`publications-config` に対応した最新版の `firestore.rules` をFirebaseへ公開する必要があります。
- 管理者ダッシュボードやFirestoreルールを変更した場合は、`引き継ぎ書.md` もあわせて更新してください。
- GitHub Pagesの公開反映には数分かかる場合があります。Actions / Pages のデプロイジョブが queued の間は、公開URLが古い画面を返すことがあります。
