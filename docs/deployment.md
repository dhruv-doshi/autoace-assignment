# P6 deployment guide

**Pricing checked:** 2026-08-01

## Recommended deployment

Render Standard is the simplest production-oriented choice for this build:

- 1 CPU and 2 GB RAM;
- predictable **$25/month** instance cost;
- Docker builds, Git branch deployments, health checks, managed TLS, custom
  domains, and zero-downtime deploys;
- `render.yaml` already deploys the `prod` branch and checks
  `/_stcore/health`.

The final P6-only regression profile peaked at 927.1 MB on the longest supplied
call (the primary live experiment recorded 891.5 MB), so Render's 512 MB
Free/Starter instances are not suitable. The 2 GB Standard instance preserves
useful headroom.

Official references:

- https://render.com/docs/compute-plans
- https://render.com/articles/top-heroku-alternatives-agencies
- https://render.com/docs/blueprint-spec

## Required secrets

Configure these in the hosting platform; never commit them:

| Variable | Purpose |
|---|---|
| `AUTOACE_DASHBOARD_PASSWORD` | Dashboard access control |
| `OPENROUTER_API_KEY` | P6 Gemini audio request |

Optional controls:

| Variable | Default | Purpose |
|---|---:|---|
| `AUTOACE_OPENROUTER_BUDGET_USD` | `0.10` | Hard external-spend cap per dashboard run |
| `AUTOACE_MAX_FILES_PER_RUN` | `25` | Sequential batch limit |
| `AUTOACE_WHISPER_MODEL_PATH` | `models/faster-whisper/tiny` | Local pinned ASR path |

## Render steps

1. Push `main`, `prod`, and `archive/all-pipelines` to a Git host.
2. In Render, create a Blueprint from this repository.
3. Confirm that the Blueprint selects branch `prod` and plan `standard`.
4. Enter the two required secrets when prompted.
5. Deploy and wait for `/_stcore/health` to become healthy.
6. Run one non-confidential smoke file and verify the CSV download and
   recorded cost.

The filesystem is ephemeral. Dashboard run artifacts are operational evidence
only and will disappear after a restart unless an external log/object store is
added.

## Low-cost deployment: Fly.io

For a low-traffic dashboard or trial evaluation, use the included `fly.toml`.
It runs one 2 GB shared-CPU machine and automatically suspends it when idle,
then starts it when the next request arrives. The configuration preserves
memory headroom while billing only for active time; users will see a brief cold
start after idling.

The tested peak memory was about 927 MB, so a continuously running 2 GB machine
is the safer choice. A 1 GB machine may fit a light request but leaves too
little headroom for the longest observed call and is not recommended for
production.

Before first deploy:

```bash
brew install flyctl
fly auth login
# Set a globally unique name in fly.toml, then create the matching app:
fly apps create your-unique-app-name
fly secrets set OPENROUTER_API_KEY="your-openrouter-key" \
  AUTOACE_DASHBOARD_PASSWORD="choose-a-strong-password"
fly deploy
```

Keep the two secret values out of `fly.toml` and Git. `fly deploy` builds the
Docker image, installs FFmpeg, and downloads the pinned Faster-Whisper Tiny
model automatically. Gemini runs through OpenRouter and therefore requires no
local model download.

## Other reasonable options

| Platform | Rough hosting cost | Fit |
|---|---:|---|
| Fly.io shared CPU, 2 GB | about **$11–$17/month** depending on region, plus network | Lowest always-on compute estimate; more operational setup |
| Railway Hobby, up to 2 GB | roughly **$20–$40/month** if kept always on, depending on measured CPU use, plus egress | Very easy Docker deploy; usage-based bill |
| Streamlit Community Cloud | **$0** | Excellent demo/trial; hibernates, variable resource limits, and not the preferred confidential production host |
| Render Standard, 2 GB | **$25/month** | Recommended balance of simplicity, predictable cost, and headroom |

Official pricing references:

- Railway: https://railway.com/pricing
- Fly.io: https://fly.io/docs/about/pricing/
- Streamlit Community Cloud:
  https://docs.streamlit.io/deploy/streamlit-community-cloud

Streamlit Community Cloud currently documents approximate memory limits up to
2.7 GB, but limits can change and apps hibernate after inactivity. It can use
`requirements.txt`, `packages.txt`, and `.streamlit/config.toml` from this
repository. The pinned Whisper model will download on the first analysis if it
is not already present.

## Total operating-cost examples

Observed P6 external inference cost was approximately
**$0.00039–$0.00069 per audio minute**. Hosting is separate.

| Monthly analyzed audio | Estimated P6 inference | Render Standard total |
|---:|---:|---:|
| 1,000 minutes | $0.39–$0.69 | about $25.39–$25.69 |
| 10,000 minutes | $3.90–$6.90 | about $28.90–$31.90 |
| 100,000 minutes | $39–$69 | about $64–$94 |

These figures exclude bandwidth, taxes, provider price changes, and any
external storage/monitoring.

## Security and operational notes

- P6 sends normalized audio to OpenRouter. Confirm retention, deletion,
  regional processing, DPA, and customer consent before confidential use.
- The built-in password is suitable for a controlled trial, not enterprise
  identity. Put the app behind platform SSO, Cloudflare Access, or an identity
  proxy for wider production use.
- Process one file at a time. Do not raise concurrency until memory profiling
  demonstrates safe headroom.
- Rotate both secrets after any accidental disclosure.
- Add durable audit storage before relying on local run artifacts.
