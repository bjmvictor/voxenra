# Slice and 4D playback validation — 2026-09-15

## Behavior

- Standard 2D scenes: loop through the active Stack or independent Axial / Coronal / Sagittal view.
- MPR: loop along the active plane's navigation direction and retain linked spatial positioning. Includes standalone PET MPR; its transactional batch must commit before the next tick.
- CT 4D: loop through temporal phases at a fixed spatial position. The label and play / stop icons carry a 4D marker.
- Expanded and collapsed toolbars both start / stop playback. The expanded panel sets 1–15 FPS (default 2). Stop retains the current position. Switching the active view or tab, disposing a tab, or encountering a render failure stops playback. Single images cannot play.
- Playback is render-paced: a timer tick does not enqueue another frame while its predecessor is pending. The FPS setting is a requested maximum, not a guaranteed rendering rate.
- Comparison tabs, 3D views, montage and fusion do not gain a playback entry in this change. MR slice playback does not imply MR temporal 4D support.

## Real CT data

Local source: `Documents/test_dicom/10-21-1997-NA-p4-86157.7z` (read-only; extracted under `/tmp` for validation).

The archive contains ten CT series with 149 slices per phase and ten accompanying RTSTRUCT objects. CT descriptions use `P4^P101^S300^I00003, Gated, 0.0%A` through `90.0%A`. Common explicit temporal tags are absent. The existing description parser did not recognize this format. Several phases also share ContentTime values, so timestamp fallback must not take precedence over the explicit gated percentages.

The scanner now recognizes the gated percentage, removes the varying terminal vendor `^I` identifier from the grouping key, and retains the existing study, frame of reference, modality and full slice-geometry checks. Phase ordering follows percentage. RTSTRUCT objects are not treated as image phases.

Native macOS QML verification:

1. Selected a CT series and clicked the actual **4D** navigation button; the tab reached ready state.
2. Loaded all ten phases. All ten displayed axial pixel hashes differed, while the shared patient-space center remained unchanged.
3. Clicked expanded Play / Stop, verified wrapping from the last phase to the first, then clicked the collapsed Play / Stop button and checked its 4D stop icon.
4. No QML warnings occurred. Screenshots were visually reviewed locally; source images and screenshots are not committed.

## Real MR data

Local source: `Documents/test_dicom/Voxenra-MR-TestData/Thin-3D-T1`.

Verified last-to-first wrap and stop for original Stack (192 images), independent 2D Axial / Coronal / Sagittal (264 / 256 / 203 samples), and all three linked MPR planes. Resliced sample counts reflect physical patient-space sampling rather than the original instance count.

## Navigation correction

Playback regression exposed a half-sample navigation error in independent sagittal views: moving relative to a rounded index could repeat a sample. Reslice geometry now carries the first navigation sample's physical offset. Slice selection targets that physical grid directly, without changing image intensities or rounding measurement values.

## Automated checks

Tests exercise real asynchronous render requests, last-to-first wrapping, render backpressure, stop and view/tab switching, single-image rejection, decode failure, linked MPR movement, PET transactional rendering, gated phase ordering with repeated timestamps, and real QML mouse clicks in both toolbar layouts.

Final coverage: **1,659 passed, 52 skipped** across the full suite and targeted reruns. The first full run hit 27 localhost-server permission errors in the sandbox and one tooltip-name assertion; permitted localhost reruns and the corrected tooltip passed. No unresolved failures remain. A separate native Cocoa control run passed **13 tests**.
