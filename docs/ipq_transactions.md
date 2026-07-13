# MediaTek IPq Transactions

`vendor.mediatek.hardware.pq.IPq/default` is a live NDK AIDL Binder service on
the XGIMI H20. The exported `BpPq` symbols in
`vendor.mediatek.hardware.pq-V1-ndk.so` reveal method names and the generated
stub contains the transaction numbers passed to `AIBinder_transact`.

Extraction:

```bash
scripts/extract_ipq_transactions.py libs/vendor.mediatek.hardware.pq-V1-ndk.so
```

## Confirmed Live Read

`getHdrType` is transaction `0x3b` / `59`.

```bash
adb -s 192.168.0.223:5555 shell \
  service call vendor.mediatek.hardware.pq.IPq/default 59 i32 4 i32 0 i32 0
```

Observed on the powered projector with the raw `service call` ABI:

```text
PQ id 0..3 -> status=0, return_code=0, hdr_type=0
PQ id 4..8 -> status=0, return_code=3, hdr_type=0
```

Interpretation: the higher PQ ids are accepted differently by the native service
than ids `0..3`, but this raw call does not yet expose the visible HDR10 picture
profile. `return_code=3` is also returned by `setHdrType(4, 3)`.

`getGlobalNonAwarePqSetting` is transaction `0x36` / `54` and returns the active
native PQ status JSON:

```bash
scripts/xgimi_h20_adb.py -s 192.168.0.223:5555 pq-get-global-settings
```

Observed live decode:

```text
decoded: status=0 return_code=0 json_length=2896
Picture_Mode=ImaxEnhanced
Backlight=50
Brightness=50
Contrast=50
Gamma=Dark
Color_Temperature=User
AI_PQ=Off
MJC_Effect=User
Local_Contrast=Off
```

This read path is now used by the Home Assistant integration's
`get_native_pq_status` service.

Important live finding: this `Picture_Mode` field is not the visible OSD picture
mode. During a manual OSD switch from `Lebhaft` to `Spiel`, logcat reported
`PqModeManager: getPQMode() called = Game`, while `getGlobalNonAwarePqSetting`
continued to report `Picture_Mode=ImaxEnhanced`. Home Assistant therefore keeps
this value only as a diagnostic sensor and no longer exposes it as a native
picture-mode select from `v0.1.12` onward.

Minimal write patches apply when the JSON string is correctly quoted through
the Android shell:

```text
0xa0 / 160 setPqParamsByGlobal({"Backlight":40}) -> status=0 return_code=0
```

Live control test:

```text
Backlight 40 -> 41 -> 40
readback after each write matched the requested value
```

The Home Assistant integration now exposes this through
`xgimi_control_bridge.set_native_pq_value`.

## High-Value Transactions

```text
0x36 / 54   getGlobalNonAwarePqSetting(out EN_RETURN_VALUE[], out string[])
0x39 / 57   getGlobalRange(string, out EN_RETURN_VALUE[], out string[])
0x3b / 59   getHdrType(int, out EN_RETURN_VALUE[], out EN_PQ_HDR_TYPE[])
0x3c / 60   getHdrTypeByWinId(int, out EN_RETURN_VALUE[], out EN_PQ_HDR_TYPE[])
0x46 / 70   getPQNonLinear(string, out EN_RETURN_VALUE[], out string[])
0x47 / 71   getPerstreamRange(string, out EN_RETURN_VALUE[], out string[])
0x4d / 77   getPresetGlobalPqParams(string, out EN_RETURN_VALUE[], out string[])
0x4e / 78   getPresetPerstreamPqParams(string, out EN_RETURN_VALUE[], out string[])
0x8a / 138  setHdrType(int, EN_PQ_HDR_TYPE, out EN_RETURN_VALUE)
0x89 / 137  setHSYUIValue(ST_HSY_ACTOR_INPUT, out EN_RETURN_VALUE[], out ST_HSY_ACTOR_OUTPUT)
0x92 / 146  setMode(int, DisplayModeSettingData, out EN_RETURN_VALUE)
0x97 / 151  setPQNonLinear(string, out EN_RETURN_VALUE)
0x9a / 154  setPqGlobalHdrType(ST_PQSETTING_INFO[], out EN_RETURN_VALUE)
0x9b / 155  setPqHWParams(int, string, out EN_RETURN_VALUE)
0x9c / 156  setPqHWParamsByGlobal(string, out EN_RETURN_VALUE)
0x9e / 158  setPqParamResult(string, out EN_RETURN_VALUE)
0x9f / 159  setPqParams(int, string, out EN_RETURN_VALUE)
0xa0 / 160  setPqParamsByGlobal(string, out EN_RETURN_VALUE)
0xa1 / 161  setPqParamsByID(int, string, out EN_RETURN_VALUE)
0xa2 / 162  setPqParamsByTarget(string, string, out EN_RETURN_VALUE)
0xa4 / 164  setPqRepositoryById(int, bool, string, out EN_RETURN_VALUE)
0xa5 / 165  setPqRepositoryByPkg(string, bool, string, out EN_RETURN_VALUE)
```

These are the first native candidates for direct HDR picture mode, MEMC,
brightness, gamma, color temperature, HSY/color tuning, and AI picture without
DPAD/menu automation.

Full-profile repository writes were tested with transaction `165`
`setPqRepositoryByPkg("com.mediatek.tv.settings", true, json)` and transaction
`162` `setPqParamsByTarget(target, json)`. They returned success for several
targets, but changing the embedded `Picture_Mode` did not change the visible
OSD mode and readback stayed on `ImaxEnhanced`. The visible mode is likely held
behind the privileged `com.mediatek.tv.settingspqdb` provider or an equivalent
privileged `PqModeManager` path.

## setMode Probe

`DisplayModeSettingData` was reconstructed from
`vendor.mediatek.hardware.pq-V1-ndk.so` as an AIDL parcelable with this payload:

```text
int32 parcelable_size
int32 displayModeType
int32 inputSourceType
int32 outputVideoFormat
bool  lowLatency
int32 field4
int32 field5
```

The Bridge APK exposes a diagnostic action:

```bash
scripts/xgimi_h20_adb.py -s 192.168.0.223:5555 bridge-pq-set-mode
```

Live result on Android 14:

```text
Command failed: java.lang.IllegalArgumentException parcel_backend=Parcel.obtain(IBinder)
```

The failure happens at `BinderProxy.transact(...)`, before
`vendor.mediatek.hardware.pq-impl.so` logs `PQ::setMode`. In other words, a
normal sideloaded APK cannot currently use this vendor Binder transaction even
when the Java parcel is created with Android 14's binder-aware
`Parcel.obtain(IBinder)` path.

A shell-launched Java helper was also added to the APK and can be invoked with:

```bash
scripts/xgimi_h20_adb.py -s 192.168.0.223:5555 bridge-pq-set-mode-shell
```

Live result:

```text
app_process ... -> Error changing dalvik-cache ownership / Killed
dalvikvm32 ...  -> ServiceManager native_get_int UnsatisfiedLinkError
```

So the next viable direct `setMode` path is a small native Android executable
built with the NDK and run from ADB shell, or a privileged/system-signed bridge
running in the same trust domain as MediaTek/XGIMI settings.
