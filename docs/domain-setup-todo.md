# Domain Setup Todo

## Current Status

- [x] Backend VM is running at `34.118.0.112`
- [x] `api.ad-diagnosis.site` resolves to the VM IP
- [x] `https://api.ad-diagnosis.site/health` responds publicly
- [x] Clerk backend verification is configured on the VM
- [x] Backend Clerk issuer now points to `https://clerk.ad-diagnosis.site`
- [x] HTTPS reverse proxy is running on the VM with Caddy
- [ ] Frontend is deployed on Vercel
- [ ] `ad-diagnosis.site` is connected to Vercel
- [ ] `www.ad-diagnosis.site` is connected to Vercel
- [ ] Backend CORS includes the final Vercel production URL

## What You Need To Do

### Cloudflare

- [x] Add `api.ad-diagnosis.site` as an `A` record pointing to `34.118.0.112`
- [x] Keep `api` as `DNS only` during initial backend bring-up
- [x] Make sure inbound `80` and `443` are open to the VM at the cloud firewall level
- [x] Add the frontend domain records exactly as Vercel asks for them
- [ ] Decide whether the primary frontend URL should be `www.ad-diagnosis.site`

### Vercel

- [ ] Import this repo from GitHub
- [ ] Set the root directory to `apps/web`
- [ ] Add `ad-diagnosis.site`
- [ ] Add `www.ad-diagnosis.site`
- [ ] Set the production env vars:

```bash
VITE_API_BASE_URL=https://api.ad-diagnosis.site
VITE_CLERK_PUBLISHABLE_KEY=pk_test_bGl2ZS1hYXJkdmFyay04OC5jbGVyay5hY2NvdW50cy5kZXYk
```

- [ ] Deploy once and confirm the site loads

## What I Need From You Later

- [ ] Final Vercel production URL if it differs from `www.ad-diagnosis.site`
- [ ] Confirmation of which hostname should be primary:
  - `ad-diagnosis.site`
  - `www.ad-diagnosis.site`

## What I Will Do After That

- [ ] Add the final frontend domain to backend `ADND_CORS_ORIGINS`
- [ ] Restart the VM backend
- [ ] Verify frontend sign-in with Clerk
- [ ] Verify an authenticated upload reaches the API
- [ ] Verify a signed-in user can open their jobs and reports

## Recommended Final Shape

- Frontend: `https://www.ad-diagnosis.site`
- Backend API: `https://api.ad-diagnosis.site`
- Apex redirect: `https://ad-diagnosis.site` -> `https://www.ad-diagnosis.site`

## Notes

- The backend is already enforcing Clerk auth on protected routes.
- The backend already has HTTPS termination on `api.ad-diagnosis.site` through Caddy.
- The frontend must send Clerk Bearer tokens to the API.
- We do not need the Clerk secret key in the browser.
- If you later move Clerk to a custom production auth domain, we will update the backend issuer and JWKS URL.
