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
- Picture/HDR/MEMC/color control: MediaTek `setPqParams*` and repository
  transactions are identified, but minimal JSON write patches currently return
  `return_code=3`; the exact firmware payload shape still needs reconstruction.
