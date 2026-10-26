# Shorts shortlist — Carmen Li × Drew Pletcher (Lightning AI)

Source: `footage/Ignite Oct 2026/07 Carmen Li Compute Exchange &Drew Pletcher Lighting.mp4` — 14:11,
1920×1080, 23.976 fps. Carmen (Silicon Data / Compute Exchange) hosts; Drew (Lightning AI, merged
with Voltage Park; ex-Cisco, ex-HFT) is the guest. Timestamps are **source time** (whisper segment
starts, ±0.3s — trim by ear). Full timestamped script: `script.txt`.

Framing note: multi-cam singles with a baked-in letterbox (rows 34–1046). Wide shot: Carmen left,
Drew right. A 9:16 crop has to re-centre per shot.

## Picks (ranked)

| # | Title / hook | In → Out | Length |
|---|---|---|---|
| 1 | **"Same GPUs, 5–8% faster"** | 4:19.4 → 5:08.7 | 49s |
| 2 | **"Coalition of experts"** | 12:54.5 → 13:48.0 | 54s |
| 3 | **"Prefill vs decode: split inference across chips"** | 8:35.9 → 9:26.4 | 51s |
| 4 | **"Here's my model, here's my data, go train it"** | 11:16.3 → 11:54.0 | 38s |
| 5 | **"Inference is about to outgrow training"** | 7:24.9 → 8:20.6 | 56s |
| 6 | **"Over 90% occupancy"** | 10:00.6 → 10:41.0 | 40s |

1. **5–8% faster** — opens "One of our key foundation labs has identified… they see a five to 8%
   higher performance in our environment on the same hardware than they do in other neoclouds."
   Carmen mishears "5 to 8x", Drew corrects: "five to 8% when you're talking about training
   mixture-of-experts models… trillions of parameters, that's huge." Concrete number, a built-in
   correction beat. Strongest clip.
2. **Coalition of experts** — "What we're hearing about is this next generation of what's called a
   coalition of experts." Prompt fans out to each department's expert network, an orchestration
   layer brings it back. Payoff: "If I'm a CEO… what's happening with the $50 million I threw at
   this new product?" → Carmen: "So you're not a neocloud anymore, you're an intelligent cloud."
   "We have to be."
3. **Prefill vs decode** — "Today you're working with general-purpose GPUs… there's the prefill,
   which is compute intensive, and the decode, which is memory intensive." Disaggregated
   inference, "roughly 40 companies out there today" building optimized chipsets; closes on
   "these are the changes we're starting to build towards now." Explainer with a number.
4. **Go train it** — "In many cases the enterprises aren't going to have those skill sets… they'll
   look for the neoclouds… here's my model, here's my data, go train it." Ends "a fully trained,
   inference-ready model." Shortest, quotable line.
5. **Inference outgrows training** — "We've been pretty much an Nvidia shop." Training has been the
   majority of workloads; low double digits a year vs. "by 2030… a 40% year-over-year growth just
   in inference." *Optional cold open:* Carmen 7:19.7 "Are you agnostic with the design houses of
   the chips?" (≈5s).
6. **90% occupancy** — Carmen: "What do you think about utilization today and how can we get
   better?" Drew: "We're greater than 90% occupancy… you will hear announcements on additional
   locations." Ends on efficiency depending on how well customers optimize their workloads.

## Bench

- **What makes a neocloud succeed** — 3:02.7 → 4:04.3 (61s; trim the question to get under 60).
  "The reference architecture is a starting place, not locked into stone." Overlaps #1's theme.
- **Bare metal vs managed Slurm** — 6:31.5 → 7:18.8 (47s). Solid but no hook line.
- **HFT vs AI: tick-to-trade vs time-to-first-token** — 1:51.0 → 2:34.6 (44s). Opens on "Because";
  needs setup.

## Transcript mis-hearings to fix if these get captioned

"Joe"/"Joo" (host addressing the guest) → probably "Drew" (filename says Drew Pletcher; whisper
hears Joe even when prompted with Drew) · "new cloud" / "Neo Clouds" → neocloud(s) ·
"pre-fill" → prefill · "infers and agenda workloads" → inference and agentic workloads ·
"bad metal" → bare metal · "Lighting" (filename) → Lightning AI · "for trading, or for training"
(self-correction) · "5 to 8x" is Carmen's real mishearing, not a transcription error.
