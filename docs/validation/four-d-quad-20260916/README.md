# 4D playback with a native 3D reference — 2026-09-16

The controller already delivered temporal volumes to the reference view, but playback only waited for MPR reslicing. Native buffer preparation and GPU presentation were not part of its pacing. Each volume replacement also switched to the loading page, and selecting 3D replaced the tool list with one that omitted temporal playback.

## Changes

- The native host tracks the volume data key of its last successfully drawn frame. Preparing buffers or uploading VTK input alone does not count as presentation.
- Visible four-view 4D playback waits for that frame before requesting another phase. Hidden native surfaces do not block slice-only playback; a native rendering error stops playback.
- The preceding 3D frame stays visible while preparing the next temporal volume, instead of switching to the loading page every phase.
- The selected 3D view exposes 4D Play / Stop in expanded and compact toolbars. Both tool controllers honor the playback lock and unlock on stop.
- Camera, display preset/window, and shared MPR position are preserved across phases. Actual FPS remains bounded by the slowest rendering stage.

## Real native verification

Source: the local `10-21-1997-NA-p4-86157` CT sample, ten phases with 149 slices per phase. No source data was modified.

Using the full QML main window and native Cocoa/VTK rendering:

- Opened 4D and the four-view layout; all ten phases produced distinct captured 3D image hashes.
- Camera and display state remained unchanged while selecting each phase.
- Selected the 3D view and clicked the expanded Play / Stop controls, then repeated through the compact toolbar and verified the 4D stop icon.
- At 2 FPS, 12 phase commits matched 12 presented 3D phases, with no loading-page flashes.
- At requested 15 FPS with an additional 150 ms preparation delay on the worker, 12 phase commits still matched 12 presented 3D phases, with no loading-page flashes. Every next-phase request observed the preceding GPU frame as ready.
- No QML warnings were reported. Captures and the native run report remain under `/tmp/voxenra-quad-validation` and are not committed.

Unit and integration regressions cover GPU completion versus buffer readiness, slow preparation, hidden views, native errors, tool locking, QML clicks, ordinary CT/PET MPR, standalone volume display/editing, workspace persistence, and earlier slice playback.

Final targeted regression: **214 passed, 3 skipped**. Native 3D validation passed at both normal and deliberately slower preparation rates.
