# 日商簿記2級 仕訳トレーニングアプリ

大学生向けの日商簿記2級・仕訳問題反復学習アプリです。学生用アプリはGitHub Pagesで公開し、学習記録はブラウザ内保存とFirebase同期コードで扱います。管理者はFirebase Authenticationでログインし、大学別・学籍番号別の成績を確認できます。

## 公開URL

- 学生用アプリ: https://urutoraktiti-boop.github.io/boki-shiwake-app/
- 管理者ダッシュボード: https://urutoraktiti-boop.github.io/boki-shiwake-app/admin/
- 学生向けデータ引き継ぎガイド: https://urutoraktiti-boop.github.io/boki-shiwake-app/help/

## 主なファイル

| ファイル | 役割 |
|---|---|
| `index.html` | 学生に配布する公開版。問題49問を同梱 |
| `src/仕訳学習アプリ.html` | 開発マスター版。編集は基本的にこちらへ行う |
| `src/問題セット_第1問特集①-⑨.json` | 問題データ原本 |
| `admin/index.html` | 管理者用成績ダッシュボード |
| `admin/invite.html` | 管理者招待後の確認ページ |
| `firestore.rules` | Firestoreセキュリティルール |
| `引き継ぎ書.md` | 詳細な仕様・運用メモ・次回開発者向けの引き継ぎ |

## 更新時の注意

- 学生用アプリの改修は、まず `src/仕訳学習アプリ.html` を編集します。
- 配布版を更新するときは、マスター版の `BUNDLED_SETS` に `src/問題セット_第1問特集①-⑨.json` を注入して `index.html` を再生成します。
- 管理者が学生画面を確認するときは、管理者ダッシュボードの「確認用に開く」を使います。このURLには `preview=admin` が付き、初回登録ポップアップを出しません。
- 管理者ダッシュボードやFirestoreルールを変更した場合は、`引き継ぎ書.md` もあわせて更新してください。
- GitHub Pagesの公開反映には数分かかる場合があります。Actions / Pages のデプロイジョブが queued の間は、公開URLが古い画面を返すことがあります。
