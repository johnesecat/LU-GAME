# HyperDeep → Web (WASM/WebGPU, Bevy/Rust) Port — Task List

## Phase 0 — Recon (REA + filesystem)
- [x] Inventory workspace (HyperDeep.exe launcher, HDT/ game, Engine/, port-example/)
- [x] Identify HDT as Unreal Engine packaged game (HDT-Win64-Shipping.exe, 340MB .pak, KawaiiPhysics plugin)
- [ ] Extract .pak contents (uasset/uexp/ubulk) — need UE4 pak parser
- [ ] REA analysis of HyperDeep.exe (launcher) — confirm it just spawns HDT
- [ ] REA analysis of HDT-Win64-Shipping.exe — game logic (Blueprint-heavy, C++ shipping core)
- [ ] Enumerate assets: textures, meshes, audio, UI, maps
- [ ] Understand game mechanics (HyperDeep: dialogue/interaction sim with HD-chan)

## Phase 1 — Asset pipeline
- [ ] Parse .pak (UE4.27-ish, possibly encrypted/compressed)
- [ ] Decode .uasset/.uexp (property data, texture data, skeletal meshes)
- [ ] Convert textures → PNG/WebP
- [ ] Convert audio → ogg/wav
- [ ] Extract dialogue + presets (already have default.txt, outfit PNGs)

## Phase 2 — Bevy (Rust) reimplementation
- [ ] Cargo project: bevy 0.16/0.17, wasm32-unknown-unknown target
- [ ] WebGPU renderer (bevy_render wgpu backend), fallback WebGL2
- [ ] Game states: boot → main scene
- [ ] Character (HD-chan) rendering with outfits
- [ ] Interaction system (mouse + touch)
- [ ] Dialogue system (parse default.txt format)
- [ ] Audio playback (bevy_audio, Web Audio)
- [ ] Touch controls for iOS Safari
- [ ] Performance: asset streaming, compressed textures

## Phase 3 — Web deployment
- [ ] wasm-bindgen/wasm-pack build (no trunk/wasm-pack installed — use cargo + wasm-bindgen CLI or raw)
- [ ] index.html loader (like port-example), GitHub Pages compatible (relative paths!)
- [ ] Test locally (node http server)
- [ ] Test in browser via CDP if available

## Phase 4 — Verification
- [ ] Run headless tests (cargo test)
- [ ] Verify wasm builds
- [ ] Document controls & features
