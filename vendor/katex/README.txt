KaTeX, vendored (version 0.16.11)
=================================

What this is
-------------
KaTeX's renderer (katex.min.js, katex.min.css), its auto-render extension
(contrib/auto-render.min.js, scans arbitrary page text for $...$/$$...$$ and
renders it in place), and its woff2 web fonts only (no legacy ttf/woff).
Used by claim_dashboard.html to render the formula/statement fields of
latex_notes/structure/claims.json in the browser.

Why vendored instead of CDN-loaded
-----------------------------------
A CDN <script> tag, even pinned to an exact version, can be swapped
server-side after the fact -- this happened in 2024 when the polyfill.io CDN
was bought out and started serving malware to every site that loaded it.
Vendoring removes that trust dependency: the exact bytes that run in the
browser are committed to this repository and reviewable like any other file.

Provenance and verification
-----------------------------
Downloaded from the official npm tarball:
  https://registry.npmjs.org/katex/-/katex-0.16.11.tgz
Verified before extracting -- both hashes matched the version metadata
published at https://registry.npmjs.org/katex/0.16.11 exactly:
  sha1   4bc84d5584f996abece5f01c6ad11304276a33f5
  sha512 RQrI8rlHY92OLf3rho/Ts8i/XvjgguEjOkO1BEXcU3N8BqPpSzBNwV/G0Ukr+P/l3ivvJUE/Fa/CwbS6HesGNQ==
Only dist/katex.min.js, dist/katex.min.css, dist/contrib/auto-render.min.js,
and dist/fonts/*.woff2 were taken from the tarball -- nothing else.

Upgrading
----------
Repeat the same process against a newer pinned version (fetch the tarball,
check its hash against that version's own npm registry metadata, re-extract
the same four locations) rather than re-pointing at a CDN.
