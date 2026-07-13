# Home Assistant Target

The current custom integration lives in:

```text
custom_components/xgimi_control_bridge
```

The next native version should avoid UI automation and call confirmed firmware
interfaces through one of these paths:

1. Direct ADB binder calls for simple transaction-based controls.
2. A small Android helper APK exposing only confirmed direct calls.
3. A native helper binary only if required by MediaTek PQ binder/HIDL/AIDL access.

Confirmed candidates:

- Autofocus: direct `service call`.
- Native PQ status: direct MediaTek `IPq` transaction `54`
  (`getGlobalNonAwarePqSetting`) returns active JSON for picture mode,
  brightness, backlight, gamma, color temperature, AI picture, MEMC/MJC, and
  local contrast.
- Native PQ write: direct MediaTek `IPq` transaction `160`
  (`setPqParamsByGlobal`) accepts correctly quoted minimal JSON patches.
  Live confirmed with `Backlight` 40 -> 41 -> 40 and exposed as
  `xgimi_control_bridge.set_native_pq_value`.
- ExtService PQ status: bridge APK action `GET_EXT_PQ_SETTINGS` binds
  `com.mediatek.extservice` with `PqService.remote` and reads
  `IPqService.getGlobalPqSettings()`. This mirrors the OSD-adjacent MediaTek
  API layer and is exposed as `xgimi_control_bridge.get_ext_pq_status`.
  Live testing shows the service requires the `signature|privileged`
  `com.mediatek.tv.extservice.permission.USE_PQSERVICE` permission, so this is a
  diagnostic path for normal sideloaded installs.
- Picture/HDR/MEMC/color control: keys present in the native JSON can now be
  tested directly through `set_native_pq_value`; preset/repository APIs remain
  useful for reconstructing named picture modes.
