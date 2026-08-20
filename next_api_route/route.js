// app/api/ask/route.js  (Next.js App Router — Route Handler)
//
// THIS FILE RUNS ON THE SERVER ONLY. Its code is never sent to the browser,
// so API_SECRET never appears in any bundle, network tab, or dev-tools
// inspection — that's what makes it a real secret, unlike anything
// referenced from client-side code (e.g. anything prefixed NEXT_PUBLIC_).
//
// The browser calls THIS route (same-origin: /api/ask). This route then
// calls the real Railway backend, attaching the secret itself.
//
// Env vars to set in your Next.js project (plain names, NOT NEXT_PUBLIC_):
//   BACKEND_URL = https://your-app.up.railway.app
//   API_SECRET  = <same long random string you set on Railway>

const BACKEND_URL = process.env.BACKEND_URL;
const API_SECRET = process.env.API_SECRET;

export async function POST(request) {
  let body;
  try {
    body = await request.json();
  } catch {
    return Response.json({ detail: "Invalid JSON body." }, { status: 400 });
  }

  const backendRes = await fetch(`${BACKEND_URL}/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Api-Secret": API_SECRET,
    },
    body: JSON.stringify(body),
  });

  const data = await backendRes.json();
  return Response.json(data, { status: backendRes.status });
}
