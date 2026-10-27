# Shorts shortlist — Steven Hou × Aravindh Srikumar (Upscale AI)

Source: `footage/Ignite Oct 2026/12 Steven Hou Silicon Data and Aravindh Srikumar Upscale AI.mp4` — 10:37,
1920×1080, 23.976 fps. Steven Hou (Head of Research, Silicon Data) hosts and interviews;
Aravindh Srikumar (Upscale AI) is the guest. Timestamps are **source time** (whisper segment
starts, ±0.3s — trim by ear). Full timestamped script: `script.txt`.

Framing note: multi-cam singles + a wide with a baked-in letterbox; Steven sits left, Aravindh
right — the 9:16 crop re-centres per shot.

## Picks (ranked)

| # | Title / hook | In → Out | Length |
|---|---|---|---|
| 1 | **"Compute grew 25X. The network grew 8X."** | 1:10.2 → 2:02.2 | 52s |
| 2 | **"Does Upscale compete with NVIDIA?"** | 6:40.4 → 7:13.1 | 33s |
| 3 | ~~"The only company doing networking for AI and nothing else"~~ **removed: ad** | 8:41.5 → 9:36.8 | 55s |
| 4 | **"The network is the bottleneck"** | 2:43.1 → 3:23.1 | 40s |
| 5 | ~~"Ten generations of ASICs"~~ **removed: ad** | 9:40.5 → 10:27.2 | 47s |
| 6 | ~~"Pure-play AI networking"~~ **removed: ad** | 0:15.1 → 0:52.2 | 37s |
| 7 | **"Not one technology suits every need"** (replacement) | 7:59.2 → 8:40.6 | 30s cut |

1. **25X vs 8X** — opens "In the past six years, if you follow the trend, compute has scaled
   25X. During the same duration, network has only grown by 8X." Explains why: networking used
   to be a separate entity outside compute; in AI it has to scale linearly with it. Lands on
   "what we're trying to do is produce a large computer — it's just distributed across the data
   center." Number hook plus a clean thesis. Strongest clip. (Leading "Yeah, so" dropped.)
2. **NVIDIA** — Steven: "Do you think that competes with the solution NVIDIA provides that
   integrates their own GPUs with interconnects, NVLink?" Aravindh: "These two are complementary
   … by the way, we are a strategic partner of NVIDIA … we use their silicon to build our
   systems." Hot-name hook, a crisp answer.
   *Alt out:* run on to 8:41.5 for the "not one technology is going to suit every single need"
   close (too long as one clip; it could be its own part 2 from 7:54.4).
3. **Only AI** — "What differentiates Upscale … when should a neocloud choose Upscale?" / "We
   are the only networking company that is just doing networking for AI and nothing more … we
   don't build WAN routers … this AI domain is super huge," ending "that's one of the biggest
   differentiators."
4. **Bottleneck** — "It is essentially critical that we scale the networks … the compute is
   going to do the operations at 25X, send it across a network that is 8X, and they're going to
   wait … currently network is the bottleneck," closing on open standards and heterogeneous AI.
   Same 25X/8X numbers as #1 but a different point (the GPUs sit idle); use one if posting
   both feels repetitive.
5. **Team** — "The team that we have assembled at Upscale are network veterans who have
   produced 10 generations of ASICs … our CEO did the first Ethernet routers … our software team
   hails from all the hyperscalers," ending "very, very differentiated as compared to any other
   networking company out there."
6. **What Upscale does** — Steven's question as cold open ("for our audience who's not
   familiar, can you tell us what Upscale AI does?") then "Upscale does pure-play AI
   networking … bring in any XPU, any GPU, any NIC … build heterogeneous networks in the
   future." Company intro; weakest hook, but a useful explainer.

## Replacement round (2026-10-27): no ads

Lana deleted #3, #5 and #6 as Upscale pitches. Only one replacement passed the
"no company pitches" test without overlapping a surviving short:

7. **"Not one technology suits every need"**, 7:59.24 → 8:40.6 source (41.4s; 30.2s after the
   silence pass and one false-start cut). Opens "If you look at NVIDIA, NVIDIA is also investing
   in heterogeneous AI through Groq and others, which are enabled by Ethernet," and ends "the
   customer really has the choice to actually choose between the different technologies … scale
   the data center and … scale the AI for the future." Upscale is never named; the point is
   that NVIDIA itself is hedging beyond NVLink and no single interconnect fits every buyer. The
   false start "not one technology is going to be, as I talked about, purpose built," was
   removed (it also pointed back into the interview). Same answer as #2 but a different point:
   #2 is "complementary, we're a partner"; #7 is "even NVIDIA is going heterogeneous".

Rejected in this round:
- 2:02 → 2:43, the "CPUs on one substrate" analogy. Not a pitch, but it is the bridge between
  #1 and #4 and lands on the same 25X/8X "network hasn't scaled" point. A third short on it
  would repeat.
- Token Fabric (3:23 → 5:37), Sky Fabrics / Sky OS / Sky Command (5:37 → 6:28): product
  explainers for Upscale's own stack. Ads.
- 7:13 → 7:54: overlaps #2 and turns into "what we do for Sky Fabrics".
- 8:41 → end: the deleted #3 and #5 (differentiators, team).

## Bench

- **Sky Command: one pipe of networking** — 5:37.6 → 6:28.1 (50s). The orchestration layer
  that makes optics, cables, silicon and software look like one network. Opens on "every single
  layer that we spoke about", which points back into the interview.
- **Token Fabric announced today** — 3:23.1 → 4:41.1. Product explainer, too jargon-dense
  and too long.
- **"Not one technology suits every need"** — 7:54.4 → 8:41.5 (47s). Part 2 of #2.

## Transcript mis-hearings to fix if these get captioned

"Steve Ho" → Steven Hou · "Arvind" → Aravindh · "Neo Cloud" / "near clouds" / "NeoCloud" →
neocloud(s) · "compute a scale 25X" → compute has scaled 25X · "NVJ" → NVIDIA · "van routers" →
WAN routers · "GROC" → Groq · "hyperscale in networks" → hyperscaler networks · "sky fabrics" /
"sky OS" / "sky command" → product names, spelling unconfirmed · "UALOE" / "ESON" → likely
UALink / ESUN, check audio.
