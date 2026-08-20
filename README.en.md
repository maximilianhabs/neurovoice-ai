# NeuroVoice AI — Local Speech Biomarker System

*[Deutsche Version](README.md)*

![Status](https://img.shields.io/badge/status-active-brightgreen)
![License](https://img.shields.io/badge/License-GPL--3.0--or--later-blue)

A local, privacy-first platform for recording and analyzing speech/voice for the
**longitudinal monitoring** of neurological conditions (e.g. Parkinson's disease, dysarthria).
**Not a diagnostic tool** — the app does not provide a diagnosis or a disease score. Instead it
delivers objective, literature-grounded speech biomarkers that can be compared over time,
analogous to an EEG follow-up analysis — just based on acoustic speech features instead of
brainwave curves.

## Status

🟢 Functional analysis tool, in active self-testing — not yet used with real patients outside
of the developer's own test recordings. See [ROAD_TO_PUBLIC.md](ROAD_TO_PUBLIC.md) for the
current state on the path toward public use.

## What the app does

A guided Streamlit dashboard with four recording modules, ordered from easy to demanding, each
optional/skippable:

1. **Vocalization** — sustained vowel /a/ (mandatory), optionally /i//u/ (for vowel-space
   analysis) and maximum phonation time (MPT).
2. **Reading aloud** — standard text ("Nordwind und Sonne", a classic German IPA reference
   text), automatically transcribed (locally, see below) for speech-rate/pause metrics and
   lexical diversity.
3. **Spontaneous speech** — free speaking (~30s) in response to a graded topic prompt.
4. **Diadochokinesis (DDK)** — pa/ta/ka individually + combined, for articulation rhythm.

Each recording can be repeated multiple times (take management); the best take is selected
manually — **nothing is averaged automatically**. For each parameter the app shows the value,
reference range, status, and a context comment with a literature source, clearly labeled by
evidence tier ("well established" / "discussed in research" / "own heuristic" /
"descriptive only") — see [docs/literatur_review.md](docs/literatur_review.md) (German). An
overall report summarizes all modules of a session and can be exported as Excel/PDF.

Transcription (for speech rate/pauses/lexical measures) runs entirely locally via
[WhisperX](https://github.com/m-bain/whisperX) in its own background process — no cloud API,
no data ever leaves your own machine/server. In the reading-aloud module (known reference
text), the app additionally compares the transcription against the original text (word/
character error rate) as an approximation of speech intelligibility. There's also an F0-based
gender estimate with a confidence score, and two spectral voice-quality measures (Alpha Ratio,
Hammarberg Index) — both computed independently with the existing Praat pipeline rather than
via the (for us not usable, license-wise) openSMILE library, see
[docs/literatur_review.md](docs/literatur_review.md).

## Privacy principle

Deliberately **no name, no initials** — every session is only assigned a pseudonymous ID + age
(`core/subject_store.py`). Re-identification (which ID belongs to which real person) is left
entirely to the recording person, outside the app. **Important**: the app currently has **no
authentication layer of its own** — see [SECURITY.md](SECURITY.md) for the access model before
running it in a multi-user/networked context.

## Repo structure

- `dashboard/` — the actual Streamlit analysis dashboard (code, Docker setup)
- `docs/` — concept notes, [backlog](docs/backlog.md), [literature review](docs/literatur_review.md),
  [bug/issue tracker](docs/bugtracker.md) — **note: all files under `docs/` are in German**,
  this English README is currently the only English-language document in the repo
- `raw-inbox/`, `data/raw/`, `scripts/` — optional alternative to direct browser microphone
  recording: feed in files via Syncthing/manually and convert them losslessly to WAV via
  `scripts/convert_and_verify.sh`; the dashboard reads `data/raw/` read-only as an additional
  recording source
- `ROAD_TO_PUBLIC.md` — roadmap/checklist toward public use (German)

## Running locally (Mac/Windows, via Docker)

The complete analysis dashboard can be run entirely locally — no cloud, no external server
needed, all data stays on your own machine. Primarily developed and tested for **Apple Silicon
(M1–M5)**, but also runs on Windows (Docker Desktop with WSL2 backend) and Intel Macs — the
host operating system doesn't matter to the container itself, Docker always starts the same
Linux container everywhere; only the CPU architecture (arm64 vs. amd64) is automatically
accounted for when building.

```bash
cd dashboard
docker compose -f docker-compose.local.yml up -d --build
```

Then in your browser: **http://localhost:8501**

**Microphone access works here without any further steps.** Browsers generally refuse
microphone access (`getUserMedia`) on unencrypted origins — but `localhost` is explicitly
exempt from this per the browser specification. As long as the app and browser run on the same
machine, no HTTPS/certificate is needed. Only if you want to reach the app from **another
device** (e.g. a tablet on the same Wi-Fi) do you need real HTTPS — see
["Access from a second device"](#access-from-a-second-device-optional-microphone-over-lan)
below.

### System requirements in detail (disclaimer)

Two containers start together: the dashboard (web UI) and a separate background worker that
handles speech recognition (WhisperX), so the UI doesn't block while transcription runs (see
[docs/konzept_p9_hintergrundjob_lokal.md](docs/konzept_p9_hintergrundjob_lokal.md), German).
Both run as Linux containers on every platform — Docker makes the host OS irrelevant to the
container itself, only the CPU architecture (arm64 vs. amd64) determines which packages get
downloaded.

**General, platform-independent:**
- Internet access on the very first start — after that everything runs completely offline/locally
- Microphone access in the browser (Chrome/Safari/Edge) for your own recordings
- Recommended: at least 8 GB RAM allocated to Docker Desktop/the Docker daemon — WhisperX
  ("large-v3") needs this; with less RAM the worker container can crash (`OOMKilled`, see
  [docs/bugtracker.md](docs/bugtracker.md) INFRA-BEFUND-09, German, encountered on our own
  server)

**Download sizes (one-time, then cached):**

| Component | Size | When |
|---|---|---|
| Python dependencies (Torch CPU, WhisperX ecosystem, Streamlit, Parselmouth, …) | ~1.5–2 GB download | While building the Docker image |
| WhisperX speech model "large-v3" | ~3 GB | On the first actual transcription run (not during the build itself) |
| Finished Docker image (one service; UI + worker share the same base) | ~3.8–5.2 GB on disk, depending on platform | After building |

**Recommended total free disk space: at least 15–20 GB** — this covers the Docker image, the
speech model, AND the temporary build cache (Docker temporarily uses more space while building
than remains afterward; reclaimable afterward with `docker builder prune`).

**Per platform — empirically measured, as of 2026-08-16 (full rebuild without Docker cache):**

| Platform | Does Parselmouth need to be compiled? | Measured build time (one-time) |
|---|---|---|
| **Apple Silicon (M1–M5), primary target platform** | **Yes** — no prebuilt Parselmouth package exists for `linux/arm64`, so it's compiled from C/C++ source during the build (Praat's own code, which takes most of the time) | **~14 minutes** (almost entirely the Parselmouth compilation — everything else downloads as a prebuilt CPU package, no unnecessary GPU packages) |
| **Windows (Docker Desktop, WSL2 backend)** | No — prebuilt package available (same `linux/amd64` architecture as our production server) | Not separately measured, but structurally identical to the server rebuild — expected to be noticeably faster than arm64, likely in the low single-digit minutes |
| **Intel Mac (Docker Desktop)** | No — also `linux/amd64`, same as Windows above | Same as Windows above |
| **Linux (Ubuntu etc.) via Docker** | No, as long as `amd64` (most PCs/servers) | Same as Windows above — this is also the variant actually used and verified on our own production server (Ubuntu, Intel N150) |
| **Linux native, WITHOUT Docker** | No on amd64 (same as above) | Not separately tested — this project has so far used Docker exclusively, even on our own Ubuntu server; a native run without a container should technically work (same `apt`/`pip` packages), but this is not verified |

**Subsequent starts are fast** (seconds instead of minutes) — Docker uses its layer cache as
long as the code hasn't changed between starts.

All data (recordings, derived results, the downloaded speech model) live in Docker's own
persistent volumes — they survive a `docker compose down`/`up`, but are **not** automatically
backed up anywhere. If you'd rather have direct file access on your own host folder instead of
a Docker volume, you can set `NEUROVOICE_HOST_DATA_DIR`/`NEUROVOICE_HOST_DERIVED_DIR` via a
`.env` file (see the comments in `dashboard/docker-compose.local.yml`).

### Access from a second device (optional, microphone over LAN)

If `localhost` isn't enough — e.g. because the app runs on one machine and a tablet/second
laptop on the same network should access it — microphone access there needs real HTTPS (see
the explanation above). There's an optional [Caddy](https://caddyserver.com/) reverse-proxy
profile for this, which issues valid certificates locally (no internet, no domain needed):

```bash
cd dashboard
docker compose -f docker-compose.local.yml --profile https up -d --build
```

This starts a third container alongside the dashboard + worker, terminating HTTPS on port
**8443**. From the **same** machine, `https://localhost:8443` is then enough afterward — but
the browser will show a certificate warning until the one-time CA installation below has been
done.

**One-time: install Caddy's local certificate authority (CA)** so browsers treat it as trusted
(no trick, no internet connection needed for this — Caddy generates this CA purely locally):

```bash
docker compose -f docker-compose.local.yml --profile https cp caddy:/data/caddy/pki/authorities/local/root.crt ./neurovoice-local-ca.crt
```

<details>
<summary><strong>macOS</strong> — install certificate</summary>

```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ./neurovoice-local-ca.crt
```

Alternatively: double-click the file → Keychain "System" → open the certificate → "Trust" →
"When using this certificate" → "Always Trust".
</details>

<details>
<summary><strong>Windows</strong> — install certificate</summary>

Double-click the file → "Install Certificate" → "Local Machine" → "Place all certificates in
the following store" → "Trusted Root Certification Authorities".
</details>

<details>
<summary><strong>Linux</strong> — install certificate (Debian/Ubuntu example)</summary>

```bash
sudo cp ./neurovoice-local-ca.crt /usr/local/share/ca-certificates/neurovoice-local-ca.crt
sudo update-ca-certificates
```

Firefox/Chrome have their own certificate store separate from the system on some
distributions — import it additionally via the browser settings there if needed.
</details>

<details>
<summary><strong>Second device on the same network</strong> (tablet/phone/other laptop)</summary>

1. Transfer `neurovoice-local-ca.crt` to the second device (AirDrop, email, USB, …).
2. Install it there as a trusted root certificate (iOS: install the profile **and
   additionally** enable it under Settings → General → About → Certificate Trust Settings;
   Android: Settings → Security → Encryption & credentials → Install a certificate →
   "CA certificate").
3. Find the LAN IP of the machine running Docker (e.g. `ipconfig getifaddr en0` on a Mac),
   then open `https://<that-LAN-IP>:8443` on the second device.
</details>

**Important**: port 8443 is bound to all network interfaces by default
(`NEUROVOICE_HTTPS_BIND=0.0.0.0`, see `dashboard/.env.local.example`) — reachable from any
device on the same LAN this way, but **not** from the internet, as long as your router has no
port forwarding set up. If you want to restrict this further, you can set
`NEUROVOICE_HTTPS_BIND` in your own `.env` file to a specific IP.

Concept/alternatives (mkcert, Tailscale, why Caddy instead of Streamlit's own SSL option), see
[docs/konzept_g1_mikrofon_ohne_tailscale.md](docs/konzept_g1_mikrofon_ohne_tailscale.md)
(German).

### Core libraries used (licenses)

NeuroVoice AI builds on several external open-source projects — here are the most important
ones, with licenses as stated by their own projects (not legal advice, for orientation only).
Because of the GPL-3.0 core dependency Parselmouth, this repo itself is licensed under
**GPL-3.0-or-later** (see [LICENSE](LICENSE) and the reasoning in
[ROAD_TO_PUBLIC.md](ROAD_TO_PUBLIC.md), German):

| Library | Purpose in the project | License |
|---|---|---|
| [Praat](https://www.fon.hum.uva.nl/praat/) / [Parselmouth](https://parselmouth.readthedocs.io/) | Core acoustic analysis (jitter/shimmer/HNR/formants/…) | GPL-3.0-or-later |
| [WhisperX](https://github.com/m-bain/whisperX) | Speech recognition/transcription with word timestamps | BSD-2-Clause |
| [PyTorch](https://pytorch.org/) | Numerical backend for WhisperX | BSD-3-Clause |
| [Streamlit](https://streamlit.io/) | Web UI | Apache-2.0 |
| [pandas](https://pandas.pydata.org/) / [NumPy](https://numpy.org/) / [SciPy](https://scipy.org/) | Data processing | BSD-3-Clause |
| [Matplotlib](https://matplotlib.org/) | Visualizations | Matplotlib License (BSD-style) |
| [soundfile](https://python-soundfile.readthedocs.io/) | Audio I/O | BSD-3-Clause |
| [openpyxl](https://openpyxl.readthedocs.io/) | Excel report export | MIT |
| [fpdf2](https://py-pdf.github.io/fpdf2/) | PDF report export | LGPL-3.0-only |
| [ffmpeg](https://ffmpeg.org/) | Audio conversion | LGPL/GPL mix depending on the Debian build, see project page |

## License & contributing

- **License**: [GNU GPL-3.0-or-later](LICENSE).
- **Security/access model**: [SECURITY.md](SECURITY.md) — please read before running this yourself.
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md) (German).
- **Citation**: [CITATION.cff](CITATION.cff) (GitHub "Cite this repository").
- This project was built with the support of AI tools (Claude Code) for implementation and
  research — the author is responsible for the content, testing, and clinical/scientific
  judgment.
