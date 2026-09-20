# MTF phantom patches

`point_sources.npz` contains two 97 × 97 signed CT-intensity patches supplied for
this software's MTF audit. No DICOM headers, patient identifiers or complete
images are included. No interpolation, filtering or window/level is applied.
Pixel spacing is 0.1953125 mm in both directions; the requested point is (48, 48)
in each patch, using zero-based column/row coordinates.

- `helical_slice11`: application-sorted slice 11, requested X597/Y605.
- `qa_slice151`: `2026-09-17-01-19-24`, application-sorted slice 151, requested
  X507/Y411. The DICOM InstanceNumber is 138; file names/instance numbers are not
  the application's spatial ordering. Slicer 5.12.4 GDCM decoding of this exact
  source slice matches the application pixel for pixel.

The fixtures exercise ROI invariance and sensitivity rejection, not absolute
scanner calibration. Their expected MTF is not asserted as a certified truth.
Analytic Gaussian and sharpened-Gaussian tests provide independent numerical
accuracy checks. See `docs/validation/mtf-final-20260920.md` for methodology.
