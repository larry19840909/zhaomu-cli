"""Extract zhaomu API docs from ShowDoc — auto-discovers all pages.

1. Opens the main page, expands all sidebar sections.
2. Extracts all page IDs and names from the sidebar tree.
3. Iterates through each page, extracting clean markdown.
4. Saves to docs/api/ subdirectories by category.
"""
import os, re, time
from playwright.sync_api import sync_playwright

BASE = "https://www.showdoc.com.cn/2072093438137669"
START_URL = f"{BASE}/9333513581813676"  # first page with sidebar
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "api")
os.makedirs(DOCS_DIR, exist_ok=True)

# Category mapping: page index → subdirectory
CATEGORIES = [
    (1, 2, "01-regions"),
    (3, 6, "02-products"),
    (7, 10, "03-cloud-lifecycle"),
    (11, 23, "04-cloud-management"),
    (24, 24, "05-other"),
    (25, 31, "06-accelerator"),
]


def discover_pages(page):
    """Expand all sidebar sections, then return list of (page_id, name, index)."""
    # Recursively expand until no more collapsed sections
    for _ in range(5):
        count = page.evaluate("""() => {
            const els = document.querySelectorAll('.ant-tree-switcher_close');
            els.forEach(e => e.click());
            return els.length;
        }""")
        time.sleep(1.5)
        if count == 0:
            break

    # Extract all page nodes
    pages = page.evaluate("""() => {
        const nodes = document.querySelectorAll('[id^="node-page_"]');
        return Array.from(nodes).map(el => ({
            id: el.id.replace('node-page_', ''),
            name: el.textContent.trim()
        }));
    }""")
    return [(p["id"], p["name"], i + 1) for i, p in enumerate(pages)]


def extract_page(page):
    """Extract clean markdown from the current page's .markdown-body."""
    return page.evaluate("""() => {
        const el = document.querySelector('.markdown-body');
        if (!el) return null;
        const title = document.title.replace('--ShowDoc', '');
        const children = Array.from(el.children);
        const lines = ['# ' + title, ''];
        children.forEach(c => {
            const tag = c.tagName;
            const text = c.innerText.trim();
            if (tag === 'H5') {
                lines.push('## ' + text, '');
            } else if (tag === 'UL') {
                if (/^https?:\\/\\//.test(text)) {
                    lines.push('`' + text + '`', '');
                } else if (/^(GET|POST|PUT|DELETE)$/i.test(text)) {
                    lines.push(text.toUpperCase(), '');
                } else {
                    lines.push(text, '');
                }
            } else if (tag === 'DIV' && text.includes('\\t')) {
                const rows = text.split('\\n');
                const cols = rows[0].split('\\t');
                lines.push('| ' + cols.join(' | ') + ' |');
                lines.push('|' + cols.map(() => '--------').join('|') + '|');
                for (let r = 1; r < rows.length; r++) {
                    lines.push('| ' + rows[r].split('\\t').join(' | ') + ' |');
                }
                lines.push('');
            } else if (tag === 'PRE') {
                lines.push('```json');
                lines.push(text);
                lines.push('```');
                lines.push('');
            } else if (tag === 'DIV' || tag === 'P') {
                lines.push(text, '');
            }
        });
        let result = lines.join('\\n').replace(/\\n{3,}/g, '\\n\\n').trim();
        if (result.endsWith('## \\u5907\\u6ce8')) {
            result += '\\n\\n\\u65e0\\n';
        }
        return result + '\\n';
    }""")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        # Step 1: Discover all pages
        print("Discovering pages...", flush=True)
        page.goto(START_URL, wait_until="networkidle", timeout=30000)
        time.sleep(3)
        all_pages = discover_pages(page)
        print(f"  Found {len(all_pages)} pages:\n")
        for pid, name, idx in all_pages:
            print(f"  {idx:02d}. {name}")

        # Step 2: Extract each page
        for page_id, name, idx in all_pages:
            # Determine category subdirectory
            subdir = "06-accelerator"  # default
            for lo, hi, d in CATEGORIES:
                if lo <= idx <= hi:
                    subdir = d
                    break

            safe_name = name.replace("/", "_").replace("\\", "_").replace(":", "_")
            filename = f"{safe_name}.md"
            out_dir = os.path.join(DOCS_DIR, subdir)
            os.makedirs(out_dir, exist_ok=True)
            filepath = os.path.join(out_dir, filename)
            print(f"\n  [{idx:02d}/{len(all_pages)}] {name}", end=" ", flush=True)

            try:
                page.goto(f"{BASE}/{page_id}", wait_until="networkidle", timeout=30000)
                time.sleep(2)
                md = extract_page(page)
                if md and len(md) > 100:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(md)
                    print("OK")
                else:
                    print(f"FAIL (len={len(md) if md else 0})")
            except Exception as e:
                print(f"ERROR: {e}")

        browser.close()
    print(f"\nDone. {len(all_pages)} pages -> {DOCS_DIR}")


if __name__ == "__main__":
    main()
