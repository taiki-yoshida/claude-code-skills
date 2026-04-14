# general-prerequisites

A [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) that runs a short prerequisite check before Claude starts writing code. Distilled from the comment discussion on [伊勢川暁 (Akira Isegawa)'s Qiita article](https://qiita.com/Akira-Isegawa/items/00f23d206c504db2ac3b) "A 20-Year Engineer's Message to Amateur Vibe Coders."

---

## What it does

When you ask Claude to "build X" or start a new project, this skill surfaces unstated assumptions *before* any code gets written. It runs through a compact pre-flight checklist:

- **Is this for play or for work?** — the decisive question
- **CIA triad:** confidentiality, integrity, availability
- **LLM-specific risks:** data paths, training opt-out, prompt injection, tool poisoning
- **Cost caps** before loops
- **Legal / compliance** before scraping or storing personal data
- **Data model durability** before the first migration
- **Performance realism** before the first million rows
- **Stand on predecessors** — existing libraries, postmortems, proven patterns

The skill deliberately avoids being an exhaustive audit. The author of the source article tested passing his full checklist to an LLM and found that run-to-run variance dwarfed any benefit — long lists do not make LLMs safer. Instead, Claude picks the one or two categories that are load-bearing for the current task and surfaces those.

## Why it exists

The Qiita article that inspired this skill argues that AI has made it trivial to produce code, and that this *is itself* the danger: code that runs is not the same as code that is safe to ship. The comments under the article added three things that the main article undersells:

1. **LLM-specific risks** (`yamazombie`) — what path does your data take, is it opted out of training/monitoring, is prompt injection handled?
2. **CIA framing** (`koupoke`) — the whole article collapses into "ensure confidentiality, integrity, and availability."
3. **Hobby vs work** (`hiro949`) — the single most useful prerequisite is knowing which mode you are in.

This skill exists so Claude raises those three points *before* the user has to ask.

## Installation

```bash
# Symlink into Claude Code's skills directory
ln -s "$(pwd)/general-prerequisites" ~/.claude/skills/general-prerequisites
```

Or see the [parent README](../README.md) for other installation options.

## Triggers

Claude will load this skill when you say things like:

- "Let's start a new project"
- "Build a production app for X"
- "I want to vibe-code a tool that..."
- "Before I commit this, check it"
- "Set up a new repo for..."
- "I'm deploying this to real users"

## What Claude will do

1. Ask whether the work is a **hobby or production** if the scope is ambiguous.
2. Pick the 1–3 prerequisite categories that actually matter for the task.
3. Surface any unstated assumption *before* writing code, not after.
4. If you confirm it is a prototype, proceed with lower rigor but record that fact so prototype-grade code is not silently carried into production.

## Credits

- [伊勢川暁 (Akira Isegawa)](https://qiita.com/Akira-Isegawa) — original article
- Commenters whose points are directly encoded in this skill: `yamazombie`, `hideki`, `koupoke`, `hiro949`, `hiroakin66`, `externvoid`, `morima`, `tky529`, `syomu_ojisan`, `yonah53530`

---

# general-prerequisites (日本語版)

伊勢川暁氏の Qiita 記事「[20年戦士エンジニアから、素人バイブコーダーの皆様へ](https://qiita.com/Akira-Isegawa/items/00f23d206c504db2ac3b)」とそのコメント欄で挙がった観点を、Claude Code が実装に入る前に走らせる **プリフライトチェックリスト** としてまとめた [Claude Code スキル](https://docs.claude.com/en/docs/claude-code/skills) です。

## 何をするか

ユーザーから「X を作って」と頼まれたり、新しいプロジェクトを始めようとしたとき、このスキルはコードを書く前に暗黙の前提を表に出します。チェック対象：

- **これは遊びか、仕事か** — 一番効く一問
- **CIA トライアド：** 機密性・完全性・可用性
- **LLM 固有のリスク：** データの通信経路、学習オプトアウト、プロンプトインジェクション、ツール汚染
- ループを書く前の **コスト上限**
- スクレイピングや個人情報を扱う前の **法務・コンプライアンス**
- 最初のマイグレーションの前の **データモデルの耐久性**
- 100万行を超える前の **パフォーマンスの見積もり**
- **先人の肩に立つ** — 既存ライブラリ、失敗事例、ポストモーテム

このスキルは意図的に「全項目を網羅する監査」になることを避けています。著者自身が元記事のコメント欄で「チェックリスト全部を LLM に渡しても、LLM 実行ごとのバラツキの方が大きくて意味がない」と明言しているためです。Claude は代わりに、今回のタスクに効くカテゴリーだけを選んで先に確認します。

## なぜ存在するか

元記事の主張は、AI によってコード生成が簡単になったからこそ、「動くコード」と「出してよいコード」は別物である、というものです。コメント欄ではさらに三つの論点が補強されました。元記事がやや弱めに扱っている部分を、コメンター達が強調してくれた構図です。

1. **LLM 固有のリスク**（`yamazombie` さん）：データはどの通信経路を通るか、学習・監視・保持からオプトアウトされているか、プロンプトインジェクションやツール汚染への対策は済んでいるか。
2. **トライアドという枠組み**（`koupoke` さん）：記事全体は結局「機密性・完全性・可用性を守れ」の一言に集約される。
3. **遊びか仕事か**（`hiro949` さん）：最も効くプリフライト判断は、これがどちらのモードかを見分けること。

このスキルは、ユーザーが聞くより先に Claude の方からこれらを持ち出せるようにするためにあります。

## インストール

```bash
# Claude Code のスキルディレクトリにシンボリックリンクを貼る
ln -s "$(pwd)/general-prerequisites" ~/.claude/skills/general-prerequisites
```

他のインストール方法は [親 README](../README.md) を参照してください。

## トリガー例

次のような発話でスキルが読み込まれます：

- 「新しいプロジェクトを始めたい」
- 「本番で運用するアプリを作って」
- 「バイブコーディングで〇〇を作りたい」
- 「コミットする前に確認して」
- 「新しいリポジトリを立ち上げて」
- 「これを実ユーザーにデプロイする」

## Claude の挙動

1. スコープが曖昧なら、まず **「趣味ですか、仕事ですか？」** と確認する。
2. 今回のタスクで実際に効く 1〜3 カテゴリーだけを選ぶ。残りは明示的にスキップする。
3. 暗黙の前提があれば、コードを書く **前** にユーザーに上げる。書いた後ではない。
4. 「プロトタイプだよ」と言われたらリゴリティを落として進むが、その事実を記録しておき、プロトタイプ品質のコードを黙って本番に持ち込まないようにする。

## 謝辞

- [伊勢川暁](https://qiita.com/Akira-Isegawa) 氏 — 元記事の著者
- このスキルに直接反映されているコメント投稿者の方々：`yamazombie`、`hideki`、`koupoke`、`hiro949`、`hiroakin66`、`externvoid`、`morima`、`tky529`、`syomu_ojisan`、`yonah53530`
