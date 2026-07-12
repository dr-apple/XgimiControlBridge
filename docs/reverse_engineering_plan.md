# XGIMI H20 Reverse Engineering Plan

Goal: native Home Assistant control for XGIMI H20 without UI automation.

Target controls:

- Picture Mode
- HDR Picture Mode
- MEMC
- Color Temperature
- Brightness
- AI Picture
- Keystone
- Autofocus
- Power
- Zoom

Current conclusion:

- Autofocus is confirmed through XGIMI GMPF binder.
- Picture/HDR mode does not visibly change through the public-looking XGIMI
  `GmTvManager` methods tested so far.
- Manual HDR picture switching logs show `PqModeManager`, `DatabaseHelper`,
  `ColorSpaceManager`, and `GM_DISP_SCENE_V3::setPictureMode()`, which points
  toward the MediaTek PQ pipeline.

Priority order:

1. Reconstruct exported symbols and strings from MediaTek PQ libraries.
2. Reconstruct binder descriptors and transaction names from `*-V1-ndk.so`.
3. Inspect APK callsites for `PqModeManager`, `GM_DISP_SCENE_V3`, `Hdr HDR10`,
   `mHdrType`, `setPictureMode`, `setMemc`, and `ColorSpaceManager`.
4. Map binder transaction IDs with safe read-only calls first.
5. Build a Python/ADB probe tool with explicit dry-run logging.
6. Promote confirmed direct calls into the Home Assistant integration.

Non-goals:

- DPAD navigation.
- Menu OCR.
- Fragile UI timing automation.
