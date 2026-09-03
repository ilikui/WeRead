#!/usr/bin/env python3
"""
WeRead → Hugo 导出脚本

功能：
- 从微信读书 Skill Gateway 拉取包含笔记的书单
- 递归获取每本书的划线与想法
- 标准化笔记格式并去重
- 输出 JSON 数据文件 (static/data/weread_notes.json)
- 为每本书生成 Hugo Markdown 内容文件 (content/weread/<slug>.md)
- 通过 flomo 库拉取 Flomo 中带 #Archive/Blog 标签的 memo
- 输出 JSON 数据文件 (static/data/flomo_memos.json)，供 Memos 卡片页展示

环境变量：
- WEREAD_API_KEY: 微信读书 API 密钥
- WEREAD_API_GATEWAY: API 网关地址（可选，有默认值）
- FLOMO_AUTHORIZATION: Flomo 登录后获取的 authorization token
- FLOMO_TAG: 需要导出的 Flomo 标签（可选，默认 Archive/Blog）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import unicodedata
from flomo import Flomo, Parser
from datetime import datetime, timezone
from pathlib import Path

import requests

WEREAD_API_KEY = os.getenv("WEREAD_API_KEY", "").strip()
WEREAD_API_GATEWAY = os.getenv(
    "WEREAD_API_GATEWAY", "https://i.weread.qq.com/api/agent/gateway"
).strip()

FLOMO_AUTHORIZATION = os.getenv("FLOMO_AUTHORIZATION", "").strip()
FLOMO_TAG = os.getenv("FLOMO_TAG", "Archive/Blog").strip()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Authorization": f"Bearer {WEREAD_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

COLOR_MAP = {
    0: "default",
    1: "yellow",
    2: "green",
    3: "blue",
    4: "pink",
    5: "purple",
}


def _next_cursor(response: dict):
    """兼容多种分页字段名，提取下一页游标。"""
    cursor_keys = ["next", "nextKey", "next_key", "cursor", "synckey", "vid"]
    for key in cursor_keys:
        value = response.get(key)
        if value not in (None, "", 0, False):
            return key, value
    return None, None


def fetch_from_weread(api_name: str, extra_params: dict | None = None) -> dict:
    """调用微信读书 Skill Gateway。"""
    if not WEREAD_API_KEY:
        print("❌ 未检测到 WEREAD_API_KEY，请先配置环境变量。")
        return {}

    headers = dict(HEADERS)
    headers["Authorization"] = f"Bearer {WEREAD_API_KEY}"

    payload = {"api_name": api_name, "skill_version": "1.0.4"}
    if extra_params:
        payload.update(extra_params)

    try:
        response = requests.post(
            WEREAD_API_GATEWAY,
            headers=headers,
            data=json.dumps(payload),
            proxies={"http": None, "https": None},
            timeout=15,
        )
    except Exception as exc:
        print(f"❌ 访问网关出现网络异常: {exc}")
        return {}

    if response.status_code == 200:
        try:
            return response.json()
        except Exception as e:
            print(
                f"❌ 接口 [{api_name}] 返回非 JSON 响应，解析失败: {e}"
            )
            print(f"   响应内容前 500 字符: {response.text[:500]}")
            return {}

    print(
        f"❌ 接口 [{api_name}] 握手失败，状态码: {response.status_code}，详情: {response.text[:500]}"
    )
    return {}


def fetch_all_books(page_size: int = 100, max_pages: int = 200) -> list:
    """拉取包含笔记/划线的书单。"""
    books = []
    seen_ids = set()
    cursor_key = None
    cursor_value = None
    start = 0

    for _ in range(max_pages):
        params = {"count": page_size}
        if cursor_key and cursor_value is not None:
            params[cursor_key] = cursor_value
        else:
            params["start"] = start

        res = fetch_from_weread("/user/notebooks", params)
        page_books = res.get("books", [])
        if not page_books:
            break

        new_count = 0
        for item in page_books:
            book_info = item.get("book", {})
            book_id = book_info.get("bookId")
            if not book_id or book_id in seen_ids:
                continue
            seen_ids.add(book_id)
            books.append(item)
            new_count += 1

        if new_count == 0:
            break

        next_key, next_value = _next_cursor(res)
        if next_key and next_value is not None:
            cursor_key, cursor_value = next_key, next_value
            continue

        if len(page_books) < page_size:
            break
        start += len(page_books)

    return books


def fetch_all_highlights(book_id, page_size: int = 1000, max_pages: int = 200) -> list:
    """拉取一本书的全部划线。"""
    all_items = []
    seen_signatures = set()
    cursor_key = None
    cursor_value = None
    start = 0

    for _ in range(max_pages):
        params = {"bookId": book_id, "count": page_size, "is_all": 1}
        if cursor_key and cursor_value is not None:
            params[cursor_key] = cursor_value
        else:
            params["start"] = start

        res = fetch_from_weread("/book/bookmarklist", params)
        batch = res.get("updated", [])
        if not batch:
            break

        new_count = 0
        for item in batch:
            signature = (
                item.get("bookmarkId")
                or item.get("reviewId")
                or f"{item.get('chapterUid')}-{item.get('range')}-{item.get('markText', '')}-{item.get('noteText', '')}"
            )
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            all_items.append(item)
            new_count += 1

        if new_count == 0:
            break

        next_key, next_value = _next_cursor(res)
        if next_key and next_value is not None:
            cursor_key, cursor_value = next_key, next_value
            continue

        if len(batch) < page_size:
            break
        start += len(batch)

    return all_items


def fetch_all_reviews(book_id, page_size: int = 100, max_pages: int = 200) -> list:
    """拉取一本书的全部想法/批注。"""
    all_items = []
    seen_ids = set()
    synckey = 0

    for _ in range(max_pages):
        res = fetch_from_weread(
            "/review/list/mine",
            {"bookid": book_id, "count": page_size, "synckey": synckey},
        )
        batch = res.get("reviews") or []
        if not batch:
            break

        new_count = 0
        for item in batch:
            inner = item.get("review") if isinstance(item.get("review"), dict) else item
            if not isinstance(inner, dict):
                continue
            review_id = inner.get("reviewId") or item.get("reviewId")
            if not review_id or review_id in seen_ids:
                continue
            seen_ids.add(review_id)
            if review_id and not inner.get("reviewId"):
                inner["reviewId"] = review_id
            all_items.append(inner)
            new_count += 1

        if new_count == 0 or not res.get("hasMore"):
            break
        next_synckey = res.get("synckey")
        if not next_synckey or next_synckey == synckey:
            break
        synckey = next_synckey

    return all_items


def fetch_chapter_info(book_id) -> list:
    """获取书籍的章节目录（/book/chapterinfo）。

    返回章节列表，每项含 `chapterUid`（int）、`title`（str）、`level`（int），
    用于把划线里的数字 `chapterUid` 还原成可读章节标题。
    """
    res = fetch_from_weread("/book/chapterinfo", {"bookId": book_id})
    return res.get("chapters", []) or []


def build_chapter_map(chapters: list) -> dict:
    """构建 chapterUid -> 章节标题 的映射（int/str 双键防类型不匹配）。"""
    chapter_map = {}
    for chapter in chapters:
        uid = chapter.get("chapterUid")
        title = (chapter.get("title") or "").strip()
        if uid is None or not title:
            continue
        chapter_map[uid] = title
        chapter_map[str(uid)] = title
    return chapter_map


def _range_key(item: dict) -> str:
    return f"{item.get('chapterUid')}:{item.get('range') or ''}"


def merge_highlights_and_reviews(highlights: list, reviews: list) -> list:
    """把想法合并到对应划线中，保留独立想法。"""
    reviews_by_range = {}
    for review in reviews:
        if not review.get("range"):
            continue
        reviews_by_range.setdefault(_range_key(review), []).append(review)

    merged = []
    used_review_ids = set()

    for highlight in highlights:
        item = dict(highlight)
        matched = reviews_by_range.get(_range_key(item), [])
        comments = []
        for review in matched:
            content = (review.get("content") or "").strip()
            if content:
                comments.append(content)
            review_id = review.get("reviewId")
            if review_id:
                used_review_ids.add(review_id)
                item["reviewId"] = item.get("reviewId") or review_id
            item["chapterTitle"] = (
                item.get("chapterTitle")
                or review.get("chapterTitle")
                or review.get("chapterName")
                or ""
            )
        if comments:
            item["noteText"] = "\n".join(comments)
        merged.append(item)

    for review in reviews:
        review_id = review.get("reviewId")
        if review_id in used_review_ids:
            continue
        merged.append(
            {
                "bookmarkId": None,
                "reviewId": review_id,
                "markText": (review.get("abstract") or "").strip(),
                "noteText": (review.get("content") or "").strip(),
                "chapterTitle": review.get("chapterTitle")
                or review.get("chapterName")
                or review.get("chapterUid")
                or "",
                "style": review.get("style") or 0,
                "colorStyle": review.get("colorStyle") or 0,
                "createTime": review.get("createTime") or "",
                "chapterUid": review.get("chapterUid"),
                "range": review.get("range"),
            }
        )

    return merged


def normalize_note(raw: dict, index: int, chapter_map: dict | None = None) -> dict:
    """把原始记录标准化为统一字段。"""
    mark_text = (raw.get("markText") or raw.get("abstract") or "").strip()
    note_text = (raw.get("noteText") or raw.get("content") or "").strip()

    chapter_uid = raw.get("chapterUid")
    # 1) 优先使用显式的可读标题（merge 阶段可能 fallback 成数字 chapterUid）。
    explicit_title = raw.get("chapterTitle") or raw.get("chapterName")
    chapter_title = explicit_title.strip() if isinstance(explicit_title, str) else ""
    # 2) 否则通过章节目录把数字 chapterUid 还原成章节标题。
    if not chapter_title and chapter_uid is not None and chapter_map:
        chapter_title = (
            chapter_map.get(chapter_uid)
            or chapter_map.get(str(chapter_uid))
            or ""
        )
    # 3) 兜底：保留原始 uid（chapterUid == -1 表示全书级标记，如插图，置空）。
    if not chapter_title and chapter_uid is not None and chapter_uid != -1:
        chapter_title = chapter_uid

    style = raw.get("style") or raw.get("colorStyle") or 0
    return {
        "id": raw.get("bookmarkId") or raw.get("reviewId") or f"note-{index}",
        "chapter": chapter_title,
        "chapter_uid": chapter_uid,
        "highlight": mark_text,
        "comment": note_text,
        "color": COLOR_MAP.get(style, "default"),
        "created_at": raw.get("createTime") or raw.get("updated") or "",
    }


def slugify(text: str) -> str:
    """生成 URL 友好的 slug。"""
    text = unicodedata.normalize("NFKC", text or "")
    text = re.sub(r"[^\w\s-]", "", text, flags=re.U)
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return text.lower()[:80] or "book"


def build_export_data(books: list) -> dict:
    """构建标准导出数据结构。"""
    export_books = []
    total_notes = 0

    for index, item in enumerate(books, 1):
        book_info = item.get("book", {})
        title = book_info.get("title", "未知书名")
        author = book_info.get("author", "未知作者")
        book_id = book_info.get("bookId")

        print(f"   -> 正在提取《{title}》的划线与想法...")
        highlights = fetch_all_highlights(book_id)
        reviews = fetch_all_reviews(book_id)
        raw_notes = merge_highlights_and_reviews(highlights, reviews)

        chapters = fetch_chapter_info(book_id)
        chapter_map = build_chapter_map(chapters)

        normalized_notes = []
        for note_index, raw in enumerate(raw_notes, 1):
            normalized = normalize_note(raw, note_index, chapter_map)
            if normalized["highlight"] or normalized["comment"]:
                normalized_notes.append(normalized)

        total_notes += len(normalized_notes)
        export_books.append(
            {
                "book_id": book_id,
                "title": title,
                "author": author,
                "cover": book_info.get("cover", ""),
                "category": book_info.get("category", ""),
                "note_count": len(normalized_notes),
                "chapters": [
                    {
                        "uid": c.get("chapterUid"),
                        "title": (c.get("title") or "").strip(),
                        "level": c.get("level", 1),
                    }
                    for c in chapters
                ],
                "notes": normalized_notes,
            }
        )
        print(f"   ✅ 《{title}》导出 {len(normalized_notes)} 条。")
        if index % 20 == 0:
            print(f"   ...进度：已完成 {index}/{len(books)} 本书")

    generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "meta": {
            "generated_at": generated_at,
            "source": "wechat-reading-skill-gateway",
            "total_books": len(export_books),
            "total_notes": total_notes,
        },
        "books": export_books,
    }


def _normalize_tag(tag: str) -> str:
    """去除标签前缀 # 并去除首尾空白，便于统一比较。"""
    return (tag or "").strip().lstrip("#")


def normalize_memo(memo: "Parser") -> dict:
    """把 Flomo Parser 对象标准化为统一字段。"""
    created_at = (getattr(memo, "created_at", "") or "").replace(" ", "T")
    updated_at = (getattr(memo, "updated_at", "") or "").replace(" ", "T")
    tags = [_normalize_tag(t) for t in (getattr(memo, "tags", None) or [])]
    return {
        "id": getattr(memo, "slug", ""),
        "content": memo.text.strip(),
        "tags": tags,
        "created_at": created_at,
        "updated_at": updated_at,
        "url": memo.url,
    }


def fetch_flomo_memos(tag_filter: str = FLOMO_TAG) -> list:
    """通过 flomo 库拉取指定标签（含子标签）下的 memo，返回标准化列表。"""
    if not FLOMO_AUTHORIZATION:
        print("❌ 未检测到 FLOMO_AUTHORIZATION，请先配置环境变量。")
        return []

    authorization = (
        FLOMO_AUTHORIZATION
        if FLOMO_AUTHORIZATION.lower().startswith("bearer")
        else f"Bearer {FLOMO_AUTHORIZATION}"
    )
    client = Flomo(authorization)

    try:
        raw_memos = client.get_all_memos()
    except Exception as exc:
        print(f"❌ 拉取 Flomo memo 失败: {exc}")
        return []

    target_tag = _normalize_tag(tag_filter)
    matched = []
    for raw in raw_memos:
        parsed = Parser(raw)
        tags = [_normalize_tag(t) for t in (getattr(parsed, "tags", None) or [])]
        if not any(t == target_tag or t.startswith(f"{target_tag}/") for t in tags):
            continue
        matched.append(normalize_memo(parsed))

    matched.sort(key=lambda m: m["created_at"], reverse=True)
    return matched


def build_memos_export_data(memos: list, tag_filter: str) -> dict:
    """构建 Memos 标准导出数据结构。"""
    generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "meta": {
            "generated_at": generated_at,
            "source": "flomo",
            "tag_filter": tag_filter,
            "total_memos": len(memos),
        },
        "memos": memos,
    }


def write_memos_outputs(
    data: dict,
    site_dir: Path,
    json_name: str = "flomo_memos.json",
) -> Path:
    """输出 Memos JSON 数据文件。"""
    static_data_dir = site_dir / "static" / "data"
    static_data_dir.mkdir(parents=True, exist_ok=True)

    json_path = static_data_dir / json_name
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"📦 Memos JSON 已输出: {json_path}")
    return json_path


def generate_memos_index_page(content_dir: Path) -> Path:
    """生成 content/memos/_index.md 主入口。"""
    content_dir.mkdir(parents=True, exist_ok=True)
    index_path = content_dir / "_index.md"
    index_path.write_text(
        "---\n"
        "title: Memos\n"
        "description: Flomo 卡片墙，展示带有指定标签的 memo。\n"
        "layout: memos\n"
        "---\n",
        encoding="utf-8",
    )
    return index_path


def main_export_memos(tag_filter: str):
    print(f"====== 开始通过 Flomo API 拉取 #{tag_filter} 标签下的 memo ======")
    memos = fetch_flomo_memos(tag_filter)

    if not memos:
        print("⚠️ 未能拉取到符合条件的 memo。")
        return None

    print(f"🎉 成功获取 {len(memos)} 条 #{tag_filter} memo。")
    return build_memos_export_data(memos, tag_filter)


def generate_hugo_content(book: dict, content_dir: Path) -> Path:
    """为单本书生成 Hugo Markdown 文件。"""
    slug = slugify(f"{book['title']} {book['book_id']}")
    file_path = content_dir / f"{slug}.md"

    front_matter = {
        "title": book["title"],
        "author": book["author"],
        "book_id": book["book_id"],
        "cover": book["cover"],
        "category": book["category"],
        "note_count": book["note_count"],
        "notes": book["notes"],
        "layout": "single",
        "draft": False,
    }

    lines = ["---"]
    lines.append(json.dumps(front_matter, ensure_ascii=False, indent=2))
    lines.append("---")
    lines.append("")
    lines.append(f"## 关于《{book['title']}》")
    lines.append("")
    lines.append(f"作者：{book['author']}")
    lines.append("")
    lines.append(f"共 **{book['note_count']}** 条笔记。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("> 提示：阅读页使用动态 JSON 数据展示卡片，本文件主要用于 SEO 与固定链接。")
    lines.append("")

    file_path.write_text("\n".join(lines), encoding="utf-8")
    return file_path


def write_outputs(
    data: dict,
    site_dir: Path,
    json_name: str = "weread_notes.json",
) -> dict:
    """输出 JSON 数据文件与 Hugo Markdown 内容文件。"""
    static_data_dir = site_dir / "static" / "data"
    content_dir = site_dir / "content" / "weread"

    static_data_dir.mkdir(parents=True, exist_ok=True)
    content_dir.mkdir(parents=True, exist_ok=True)

    # JSON 数据
    json_path = static_data_dir / json_name
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"📦 JSON 已输出: {json_path}")

    # 每本书的 Markdown
    written = []
    for book in data.get("books", []):
        path = generate_hugo_content(book, content_dir)
        written.append(path)
    print(f"📝 已生成 {len(written)} 本书的 Markdown 文件")

    return {"json": json_path, "markdowns": written}


def generate_index_page(content_dir: Path) -> Path:
    """生成 content/weread/_index.md 主入口。"""
    content_dir.mkdir(parents=True, exist_ok=True)
    index_path = content_dir / "_index.md"
    index_path.write_text(
        "---\n"
        "title: 阅读\n"
        "description: 微信读书笔记墙，左侧选择书籍查看划线与批注。\n"
        "layout: weread\n"
        "---\n",
        encoding="utf-8",
    )
    return index_path


def main_export():
    print("====== 1. 开始调用微信读书 Gateway 拉取包含笔记的书单 ======")
    books = fetch_all_books(page_size=100)

    if not books:
        print("⚠️ 未能成功拉取到书单。")
        return None

    print(f"🎉 成功握手！在您的账号中发现 {len(books)} 本含有划线或批注的书籍。")
    return build_export_data(books)


def parse_args():
    parser = argparse.ArgumentParser(description="WeRead / Flomo → Hugo 笔记导出脚本")
    parser.add_argument(
        "--site-dir",
        default=".",
        help="Hugo 站点根目录（默认当前目录）",
    )
    parser.add_argument(
        "--json-name",
        default="weread_notes.json",
        help="微信读书输出的 JSON 文件名",
    )
    parser.add_argument(
        "--skip-markdown",
        action="store_true",
        help="仅输出 JSON，不生成 Markdown",
    )
    parser.add_argument(
        "--skip-weread",
        action="store_true",
        help="跳过微信读书导出",
    )
    parser.add_argument(
        "--skip-memos",
        action="store_true",
        help="跳过 Flomo Memos 导出",
    )
    parser.add_argument(
        "--memo-tag",
        default=FLOMO_TAG,
        help="需要导出的 Flomo 标签（默认 Archive/Blog）",
    )
    parser.add_argument(
        "--memo-json-name",
        default="flomo_memos.json",
        help="Memos 输出的 JSON 文件名",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    site_dir = Path(args.site_dir).resolve()

    if not args.skip_weread:
        # 确保入口页面存在
        generate_index_page(site_dir / "content" / "weread")

        export_data = main_export()
        if export_data:
            write_outputs(
                export_data,
                site_dir,
                json_name=args.json_name,
            )

    if not args.skip_memos:
        generate_memos_index_page(site_dir / "content" / "memos")

        memos_data = main_export_memos(args.memo_tag)
        if memos_data:
            write_memos_outputs(
                memos_data,
                site_dir,
                json_name=args.memo_json_name,
            )

    print("\n✅ 全部完成。运行 `hugo server -D` 预览站点。")
