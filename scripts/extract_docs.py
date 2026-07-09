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

# Map Chinese page titles → English filenames
FILENAME_MAP = {
    "获取可用区列表": "list-regions",
    "获取可用区信息": "get-region",
    "获取云服务器产品列表": "list-products",
    "获取云服务器产品信息": "get-product",
    "获取云服务器产品价格": "get-product-price",
    "获取功能参数比较": "compare-products",
    "获取云服务器列表": "list-servers",
    "获取云服务器信息": "get-server",
    "订购云服务器": "order-server",
    "获取订购云服务器的镜像": "get-order-images",
    "续费云服务器": "renew-server",
    "变更云服务器": "upgrade-server",
    "获取变更云服务器价格": "get-upgrade-price",
    "销毁云服务器": "destroy-server",
    "重启/开机云服务器": "reboot-server",
    "关机云服务器": "shutdown-server",
    "重装云服务器": "rebuild-server",
    "获取重装云服务器的镜像": "get-rebuild-images",
    "重置云服务器密码": "reset-password",
    "获取云服务器控制台": "get-console",
    "设置云服务器自动续费": "set-auto-renew",
    "修改云服务器用户备注": "set-note",
    "刷新云服务器流量": "refresh-traffic",
    "获取用户余额": "get-balance",
    "获取海外服务器加速列表": "list-accelerators",
    "获取海外服务器加速信息": "get-accelerator",
    "订购海外服务器加速": "order-accelerator",
    "续费海外服务器加速": "renew-accelerator",
    "升级海外服务器加速": "upgrade-accelerator",
    "修改海外服务器加速IP": "modify-accelerator-ip",
    "修改海外服务器加速应用端口": "modify-accelerator-port",
}


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
    """Extract clean markdown from the current page's .markdown-body.
    
    Uses textContent (not innerText) to avoid UTF-8 multi-byte corruption
    that occurs when innerText reflows text across DOM boundaries.
    Tables are extracted via direct DOM traversal instead of relying on
    innerText's tab-separated rendering.
    """
    return page.evaluate("""() => {
        const el = document.querySelector('.markdown-body');
        if (!el) return null;
        const title = document.title.replace('--ShowDoc', '').trim();
        const children = Array.from(el.children);
        const lines = ['# ' + title, ''];

        // Helper: extract <table> to markdown table using textContent
        function extractTable(tableEl) {
            const rows = Array.from(tableEl.querySelectorAll('tr'));
            if (rows.length === 0) return;
            const headerCells = rows[0].querySelectorAll('th, td');
            if (headerCells.length === 0) return;
            const headers = Array.from(headerCells).map(h => h.textContent.trim());
            lines.push('| ' + headers.join(' | ') + ' |');
            lines.push('|' + headers.map(() => '--------').join('|') + '|');
            for (let r = 1; r < rows.length; r++) {
                const cells = Array.from(rows[r].querySelectorAll('td'));
                lines.push('| ' + cells.map(td => td.textContent.trim()).join(' | ') + ' |');
            }
            lines.push('');
        }

        children.forEach(c => {
            const tag = c.tagName;
            // textContent avoids innerText's CSS-aware text reflow which corrupts
            // multi-byte UTF-8 sequences at node boundaries
            const text = c.textContent.trim();
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
            } else if (tag === 'TABLE') {
                extractTable(c);
            } else if (tag === 'PRE') {
                lines.push('```json');
                lines.push(text);
                lines.push('```');
                lines.push('');
            } else if (tag === 'DIV' || tag === 'P') {
                // Check if div/p contains a table
                const table = c.querySelector('table');
                if (table) {
                    extractTable(table);
                } else {
                    lines.push(text, '');
                }
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

            safe_name = FILENAME_MAP.get(name, name.replace("/", "_").replace("\\", "_").replace(":", "_"))
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
