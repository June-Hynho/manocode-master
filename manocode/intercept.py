#FULLY_AI_GENERATED
FETCH_HOOK = r"""
(() => {
  const _fetch = fetch;

  const re = /\/conversation/i; // regex to match the url to the SSE endpoint

  fetch = async (...a) => {
    const url = typeof a[0] === "string" ? a[0] : a[0]?.url;
    const r = await _fetch(...a);

    if (!re.test(url)) return r;

    try {
      const c = r.clone();
      const reader = c.body?.getReader();
      const dec = new TextDecoder();

      if (reader) {
        (async () => {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            window.python_sse_callback(dec.decode(value, { stream: true })); // python_sse_callback exposed via page.expose_binding
          }
        })();
      }
    } catch {}

    return r;
  };
})();
"""
