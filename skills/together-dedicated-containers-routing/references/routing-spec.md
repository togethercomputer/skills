# Direct Routing Spec (v1)

Every implementation must produce the same host order for the same affinity key and host list. That
is what keeps a fleet of processes sticky to one host per key.

## Contents

Request, Affinity key, Host normalization, Ranking, Classify, Failover, Streaming, Connections.

## Request

```text
https://<router-host>/v1/deployment-request/<name>/<path>
Authorization: Bearer <TOGETHER_API_KEY>
together-affinity-key: <key>       ; optional
together-replica: <replica-id>     ; optional: a key of replica_events in the deployments API
```

- The host list from Together is authoritative: route only to listed hosts, and use the same list
  in every process. Read it through `host_source.current()`, and on refresh replace it atomically
  and drop demotion entries for hosts no longer listed.
- `<router-host>` is the normalized host on port 443: the URL host, TLS SNI and `Host` header. Never
  send one host's request to another host's address.
- The router strips `/v1/deployment-request/<name>` before your container sees the path. gRPC
  methods take the same prefix (`/v1/deployment-request/<name>/pkg.Service/Method`) over HTTP/2.
- Send `together-affinity-key` to the router too; the router keeps a key on the same replica.
- Routing data travels only in headers. If the session key lives in the body, set the header where
  the request originates.
- Non-gRPC bodies over 32 MiB get 413. A gateway may buffer a body under that cap once, to find the
  key or make it resendable, but never for gRPC or uploads.

## Affinity key

A non-empty key may contain only bytes 0x20 to 0x7E and must not start or end with a space.
Anything else fails locally: no trimming, no hashing, no request. HTTP stacks trim edge spaces and
languages encode non-ASCII differently; either would split stickiness without an error. For a
non-ASCII id, send an ASCII key such as hex or base64url of a hash of the id. An empty key counts as
absent.

## Host normalization

Normalize every entry when the list loads. The result is the hash input and the URL host.

```text
normalize(entry):
    h = entry without surrounding space, tab, CR or LF
    config error if h contains ?, #, @, [, ], space, tab, CR or LF
    h = h with ASCII A-Z lowercased
    if h contains "://":     h = the part after the first "://"   ; scheme ignored: always HTTPS
    if h contains "/":       h = the part before the first "/"
    if h ends with ":443":   drop ":443"
    config error if h still contains ":"
    if h ends with ".":      drop that one "."
    config error if h is empty
```

Two entries that normalize to the same host are a config error too. Fail at load.

## Ranking

```text
order(key, hosts):                       ; hosts normalized, key valid
    if key is empty: return a uniform random shuffle of hosts
    seed = xxh64(ascii_bytes(key), seed = 0)
    s[h] = xxh64(ascii_bytes(h), seed = seed) >> 11     for each h
    return hosts by s[h] descending; equal s[h]: lexicographically larger host by bytes first,
           where a prefix sorts lower
```

- `xxh64` is XXH64 with an unsigned 64-bit seed and result. A library that ignores or truncates the
  seed gives a plausible, wrong order. [test-vectors.json](test-vectors.json) catches it.
- `>> 11` is a logical shift on the unsigned value. Compare scores as integers: `BigInt` in
  JavaScript, and parse hex digests as unsigned.
- The first host is the key's home. List order does not matter. Removing a host moves only the keys
  homed on it.
- Hosts carry equal weight: keys split evenly whatever each host's replica count.

## Classify

Every attempt on a host is exactly one class:

| Class | Attempt | Next host | Demote |
|-------|---------|-----------|--------|
| CONNECT_FAIL | DNS, TCP connect or TLS handshake failure, or a timeout during one; nothing was sent. gRPC: the host's channel is not READY when the call would start. | If resendable | The host, all deployments |
| CONNECT_FAIL | HTTP/2 REFUSED_STREAM, or a stream above GOAWAY's last-stream-id, where the library surfaces it (a restarting router) | If resendable | None |
| REJECT 404, 503 | Router reject (below): 404 = this host does not run the deployment now; 503 = it does but cannot serve or authenticate now | If resendable | (deployment, host) |
| REJECT 410 | Router reject on a request with a non-empty `together-replica`: this host does not run that replica | If resendable | None |
| SILENT | No response headers before the header timeout, or an HTTP/2 keepalive ping timeout | No | The host, all deployments |
| RESPONSE | Anything else: your container's response, reset or EOF after sending, 400, 401, 403, 413, 502, a local pool-acquire timeout, the caller's cancel or deadline, a timeout on the first body read of a candidate reject | No | None |

A router reject has no `content-type` and ends its body on the first read. Over HTTP/1.1 it carries
`content-length: 0`; over HTTP/2 it has no `content-length`. If that first read returns data, the
attempt is a RESPONSE: pass the chunk on ahead of the rest.

gRPC sees router rejects as HTTP 200, `application/grpc`, no response message, and `grpc-status`
12 (404), 5 (410, only with `together-replica`) or 14 (router 503 or 502, only for methods the
caller marks safe to repeat: a router 502 may have reached your container, and libraries also
report a dropped connection as 14). gRPC libraries hold headers until the first message or the
trailers, so classify there. A status a call returns is never CONNECT_FAIL.

v1 resends your container's own empty-body 404, 503 or pinned 410: it cannot tell them from rejects.

## Failover

- **Commit point:** the first response byte handed to application code or written downstream.
  Never retry after it; the container may already have acted on the request.
- **Resendable:** a body in memory always is. A streamed body is only while you can prove none of it
  was consumed and can offer the same source again.
- **No extra retries.** Set SDK-level retries to zero; they would resend what the loop surfaces,
  such as a POST after a 502. The HTTP library's own retry of a stale pooled connection is fine.
- **Demotion** lasts 30 seconds by default and only expiry clears it, not a success. A demoted host
  is tried last, never skipped, and stays in the hash input.

```text
send(request):
    reject an invalid affinity key locally
    ranked = order(request.affinity_key, host_source.current())
    failures = []
    for host in ranked, demoted hosts last (relative order kept):
        attempt = forward(host, request)
        class = classify(request, attempt)
        demote per the table
        if class is CONNECT_FAIL or REJECT and the body is resendable:
            failures.append(attempt); continue
        return attempt                                ; stream it, or surface it
    return the best failure: REJECT 503 > 410 > 404 > last CONNECT_FAIL
```

Return a reject as the response itself. Never fall back to another URL.

## Streaming

- Never read a whole response body. Pass raw chunks on as they arrive, and flush each chunk of
  `text/event-stream`.
- Keep compression middleware off SSE, and turn off buffering in your own proxies (nginx
  `proxy_buffering off`, or `X-Accel-Buffering: no`).
- After the commit point, an upstream error must reach the caller as a failure: abort the
  downstream connection or stream, never end it cleanly.

## Connections and timeouts

- One pool per process, keep-alive and `TCP_NODELAY` on. Prefer HTTP/2 through ALPN (routers offer
  `h2` and `http/1.1`), with keepalive pings if the library has them. Over HTTP/1.1, keep the client
  idle timeout below a few seconds (for example 4s): routers close idle HTTP/1.1 connections early.
- Connect plus TLS: a few seconds per host.
- Header timeout: above the longest time your container takes to start a response. Expiry is
  SILENT.
- No total timeout on streams. Set an idle-read timeout per workload; the router enforces none.
- A restarting router sends `Connection: close` or GOAWAY and can cut long-running streams. A cut
  stream is past the commit point: surface it.
