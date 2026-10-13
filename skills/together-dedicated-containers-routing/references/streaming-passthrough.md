# Implementation Shapes and Language Notes

Go, Python and Node how-to for the two shapes. The rules, `classify` included, are in
[routing-spec.md](routing-spec.md). Check each API against the version you pin. An in-process hook
maps the path after the SDK's base URL to `https://<router-host>/v1/deployment-request/<name>/<path>`
per host; point the base URL at any placeholder origin.

## Gateway

```text
inbound -> affinity key from the inbound header or your session state -> order(key, hosts)
        -> forward, streaming the request body -> on RESPONSE: copy status and headers,
           then stream the body (commit point) -> on shutdown: drain in-flight streams
```

- Replace the caller's `Authorization` with your own. Never pass the inbound one through.
- Strip hop-by-hop headers both ways: `Connection`, `Keep-Alive`, `Proxy-Connection`,
  `Transfer-Encoding`, `Upgrade`, `TE` (keep `te: trailers` for gRPC), and any header `Connection`
  names.
- Forward raw bytes with the original `content-encoding`.

## gRPC

- One channel per router host (`<router-host>:443`, TLS), with an interceptor that prepends
  `/v1/deployment-request/<name>` to the method and adds `authorization` metadata.
  `together-affinity-key` and `together-replica` travel as metadata.
- CONNECT_FAIL: before the call, check the channel's connectivity state, connecting an idle channel
  within the connect timeout. If the channel drops between the check and the call, that error
  surfaces.

## Go

- One `http.Transport`. Raise `MaxIdleConnsPerHost` (default 2); keep `IdleConnTimeout` below a few
  seconds on HTTP/1.1; short `net.Dialer` timeout. A custom `TLSClientConfig`, `DialContext` or
  `DialTLSContext` needs `ForceAttemptHTTP2: true`.
- HTTP/2 pings: Go 1.24+ `Transport.HTTP2 = &http.HTTP2Config{SendPingTimeout: 30 * time.Second}`;
  earlier, `golang.org/x/net/http2` `ReadIdleTimeout`.
- Put ranking and failover in a custom `http.RoundTripper`; SDK clients and `httputil.ReverseProxy`
  share it.
- CONNECT_FAIL: a `*net.OpError` with `Op == "dial"` (DNS failures carry a `*net.DNSError`), or a
  non-nil error in `httptrace.ClientTrace.TLSHandshakeDone`, `TLSHandshakeTimeout` included. If your
  `DialTLSContext` completes the handshake itself, its TLS failure is the dial error instead.
- SILENT: `Transport.ResponseHeaderTimeout` is the header timeout. Classify by phase: before
  headers, an error with `Timeout()` true that is neither CONNECT_FAIL nor the caller's context
  ending is SILENT. Match "timeout awaiting response headers" or "client connection lost" only where
  no typed error exists.
- Leave `http.Client.Timeout` unset for streams; it covers the whole body. For idle-read, cancel the
  request context when no chunk arrives in the window.
- Streamed request body: `RoundTrip` closes `req.Body` even when the dial fails. Wrap it in a
  byte-counting reader that ignores `Close`, fail over only at zero bytes, and close the real body
  when the loop ends.
- Gateway: `ReverseProxy` with `Rewrite` (`ProxyRequest.SetURL`, then set `Authorization`). It
  flushes every write for `text/event-stream` and unknown-length responses; `FlushInterval: -1`
  does so for all. By hand: `io.Copy`, never `io.ReadAll`, and
  `http.NewResponseController(w).Flush()` after each SSE chunk.
- xxh64: `github.com/cespare/xxhash/v2` v2.3.0+, `xxhash.NewWithSeed(seed)` then `WriteString` and
  `Sum64`. `Sum64String` is the seed-0 form.

## Python

- One `httpx.Client` or `AsyncClient`. `http2=True` needs `pip install "httpx[http2]"`. Over
  HTTP/1.1, set `httpx.Limits(keepalive_expiry=4.0)`; the default 5 is too long.
- Every httpx timeout defaults to 5 seconds and cuts long streams. Set
  `httpx.Timeout(connect=3.0, read=IDLE, ...)`. `read` is per socket read: a `ReadTimeout` before
  headers is SILENT, after them it is the idle-read timeout.
- CONNECT_FAIL: `httpx.ConnectError` and `httpx.ConnectTimeout` (DNS, connect, TLS).
- Hook: subclass `httpx.BaseTransport` (`handle_request`) or `AsyncBaseTransport`
  (`handle_async_request`) around `httpx.HTTPTransport(http2=True)`, and pass
  `http_client=httpx.Client(transport=...)` to `OpenAI(..., max_retries=0)`.
- Stream with `client.stream(...)`. A gateway iterates `iter_raw()` or `aiter_raw()`, which skip
  content decoding; ASGI returns a `StreamingResponse` over `aiter_raw()` and closes the upstream
  response at the end.
- xxh64: `xxhash.xxh64_intdigest(data, seed=seed)` takes the full unsigned 64-bit seed.

## Node

- One undici `Agent`, passed as `dispatcher` to `fetch` imported from the same `undici` package.
  Node's global `fetch` bundles its own undici, and mixing versions can break.
- Agent: `allowH2: true` (default in undici 8+; undici 7, bundled in Node 24, defaults to false),
  `connectTimeout` a few seconds, `keepAliveTimeout` below a few seconds on HTTP/1.1, `headersTimeout`
  as the header timeout (`UND_ERR_HEADERS_TIMEOUT` is SILENT), `bodyTimeout` as the idle-read
  timeout. undici 8+ sends HTTP/2 PINGs by default (`h2Options.pingInterval`).
- CONNECT_FAIL: `fetch` rejects with `TypeError: fetch failed` and `err.cause.code` is
  `UND_ERR_CONNECT_TIMEOUT`, `ECONNREFUSED`, `ENOTFOUND`, `EAI_AGAIN`, `EHOSTUNREACH`,
  `ENETUNREACH`, `ETIMEDOUT` raised during connect, or a TLS certificate or alert error (such as
  `ERR_TLS_CERT_ALTNAME_INVALID`, `CERT_HAS_EXPIRED`, `ERR_SSL_*`). `ECONNRESET` and
  `UND_ERR_SOCKET` never are; a reset during the TLS handshake also arrives as `ECONNRESET` and
  surfaces.
- Pass `upstream.body` on, never `res.text()` or `res.json()`: `new Response(upstream.body, ...)`,
  or `stream.pipeline(Readable.fromWeb(upstream.body), res)` in `node:http`. `fetch` decompresses
  but keeps `content-encoding`; drop it and `content-length` when forwarding, or use
  `undici.request`, which returns raw bytes.
- A streamed request body needs `duplex: 'half'`, and that `ReadableStream` cannot be sent twice. It
  gets no failover unless the hook owns the source and can recreate it.
- Hook: `new OpenAI({ fetch: routedFetch, maxRetries: 0 })`.
- xxh64: `xxhash-wasm`, `const { h64Raw } = await xxhash(); h64Raw(bytes, seed)` with `BigInt` in
  and out. Keep scores `BigInt` through the shift and comparison.
