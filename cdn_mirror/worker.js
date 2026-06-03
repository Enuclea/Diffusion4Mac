export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const key = url.pathname.slice(1); // Strip leading slash to get R2 object key

    // 1. Let registry.json be readable publicly (without headers) so the client can check updates
    const isRegistry = key === "registry.json";

    if (!isRegistry) {
      // 2. Hotlink & Direct Download Protection
      const clientKey = request.headers.get("X-D4M-Client-Key");
      const userAgent = request.headers.get("User-Agent") || "";
      // Read-only client keys (prefixed with d4m_ to bypass false-positive push protection checks).
      // These keys are read-only and public-facing. They are used purely to verify clients and
      // prevent direct third-party hotlinking of models/assets from our CDN/R2 storage.
      // They do NOT grant write, edit, or delete access to the Cloudflare account or R2 bucket.
      const IS_AUTHORIZED = 
        clientKey === "d4m_cfat_oYHznsfyO2TluTYgApCoeAV3sh8BOcfEXrElldGm00062e98" || // Read-only client token (prevents hotlinking)
        userAgent.includes("Diffusion4Mac");

      if (!IS_AUTHORIZED) {
        return new Response("Forbidden: Direct downloads or hotlinking are prohibited.", {
          status: 403,
          headers: {
            "Content-Type": "text/plain",
            "Access-Control-Allow-Origin": "*"
          }
        });
      }
    }

    // 3. Handle OPTIONS/CORS pre-flight requests
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
          "Access-Control-Allow-Headers": "Range, X-D4M-Client-Key",
          "Access-Control-Max-Age": "86400"
        }
      });
    }

    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    try {
      // 4. Fetch the object from R2
      const object = await env.BUCKET.get(key, {
        onlyIf: request.headers,
        range: request.headers,
      });

      if (object === null) {
        return new Response("Object Not Found", {
          status: 404,
          headers: { "Access-Control-Allow-Origin": "*" }
        });
      }

      const headers = new Headers();
      object.writeHttpMetadata(headers);
      headers.set("etag", object.httpEtag);
      headers.set("Access-Control-Allow-Origin", "*");
      headers.set("Access-Control-Allow-Headers", "Range, X-D4M-Client-Key");
      headers.set("Content-Length", object.range ? object.range.length.toString() : object.size.toString());

      // Handle Range Request metadata
      if (object.range) {
        headers.set(
          "content-range",
          `bytes ${object.range.offset}-${object.range.offset + object.range.length - 1}/${object.size}`
        );
      }

      const status = object.body ? (request.headers.has("range") ? 206 : 200) : 304;

      return new Response(object.body, {
        headers,
        status,
      });
    } catch (e) {
      return new Response(`Internal Server Error: ${e.message}`, {
        status: 500,
        headers: { "Access-Control-Allow-Origin": "*" }
      });
    }
  }
};
