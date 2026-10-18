# hreflang-audit

A single-file check for the `hreflang` cluster of a page. It is built for bilingual sites (English/Arabic is our daily case), but works for any languages.

Start from one URL. The script reads its `<link rel="alternate" hreflang="…">` tags and then checks every alternate in the cluster:

| Check | Why it matters |
|---|---|
| answers `200` directly (no redirect) | annotations pointing at redirects or 404s break the set |
| not `noindex` (meta or `X-Robots-Tag`) | a noindex alternate cannot be shown |
| self-referencing canonical | a canonical to another language marks the page as a duplicate |
| lists every other member (return links) | one-way annotations are ignored |
| valid codes (`ar`, `en-AE`, `x-default`…) | `en-UK`, `ar-UAE` or `ae` are invalid |

## Usage

```bash
python3 hreflang_audit.py https://example.com/en/pricing
```

```
checked [ar] https://example.com/ar/pricing: 200, 3 annotations
checked [en] https://example.com/en/pricing: 200, 3 annotations
checked [x-default] https://example.com/en/pricing: 200, 3 annotations

cluster is consistent
```

The exit code is `1` when any problem is found, so it can run in CI after content or URL migrations.

## Limits

- It reads `hreflang` from HTML `<head>` tags only, not from XML sitemaps or HTTP `Link` headers.
- It checks the cluster of one page per run. Loop over your key templates in a shell script.
- Python 3.8+ standard library only.

The five mistakes it is designed to catch are explained in [hreflang for English and Arabic sites](https://dev.to/rokya_elbarbary_8e9bbb0da/hreflang-for-english-and-arabic-sites-the-five-mistakes-we-see-most-1m60). It is maintained by the technical SEO team at [Gorilla Vibe](https://thegorillavibe.com/service/seo).

## License

MIT
