# Findings

## Device

- Model: XGIMI H20
- Android: 14

## Confirmed Working

### Autofocus

```bash
adb shell service call xgimi.hardware.gmpf.IProjectorFocusManager/default 3 i32 2
```

Result: starts autofocus immediately.

## Confirmed Not Sufficient

The following methods exist in `/system_ext/framework/com.xgimi.api.jar`, but did
not visibly change the HDR10 picture mode in the current bridge tests:

- `setPictureMode()`
- `getPictureMode()`
- `setGamePictureMode()`
- `setMemcLevel()`
- `setPictureModeJson()`
- `setHsyPictureMode()`

Observed bridge result for picture/MEMC changes:

```text
ADB broadcast OK, app receiver OK, vendor_result=false
```

Interpretation: ADB and the bridge are working. The called XGIMI API path rejects
or ignores the active HDR picture pipeline.

## Strong Lead

Manual HDR10 picture mode switch logs:

```text
GM_DISP_SCENE_V3::setPictureMode()
ePicMode=7->0
ePicMode=0->7
Hdr HDR10
mHdrType=HDR10
```

Likely path:

```text
Settings -> PqModeManager -> JNI -> vendor.mediatek.hardware.pq-impl.so -> GM_DISP_SCENE_V3
```

## Known Services

```text
xgimi.hardware.gmpf.IProjectorFocusManager/default
xgimi.hardware.gmpf.IDisplayManager/default
xgimi.hardware.gmpf.IGmTvManager/default
xgimi.hardware.gmpf.IPowerManager/default
xgimi.hardware.gmpf.IGmAudioManager/default
xgimi.hardware.gmpf.IConfigManager/default
xgimi.hardware.gmpf.IDataBaseManager/default
```

## Useful Activity

```bash
adb shell am start \
  -n com.mediatek.tv.settings/.displayandsound.picture.PictureActivity \
  --es PictureHotKey picture_mode
```

This opens the original HDR10 picture mode page.

## Pulled Local Inputs

The following proprietary files are now present locally and ignored by Git:

```text
apks/XgimiTvSettingsVendor.apk
apks/TvAgentService.apk
apks/XRMService.apk
apks/MiscKey.apk
framework/com.xgimi.api.jar
libs/vendor.mediatek.hardware.pq-V1-ndk.so
libs/vendor.mediatek.hardware.pq-impl.so
libs/xgimi.hardware.gmpf-V1-ndk.so
libs/libPqService.so
libs/libaipqservice.so
libs/libpqactor.so
libs/libmi3_pq_hal.so
```

## MediaTek PQ Services

Additional confirmed binder services:

```text
vendor.mediatek.hardware.pq.IPq/default
vendor.mediatek.hardware.render.IRender/default
vendor.mediatek.hardware.capture.ICapture/default
vendor.mediatek.hardware.aiexecutor.IAiexecutor/default
vendor.mediatek.hardware.audioext.IAudioExt/audioext
```

## Settings PQ Database

`XgimiTvSettingsVendor.apk` and `MiscKey.apk` reference:

```text
content://com.mediatek.tv.settingspqdb/general
content://com.mediatek.tv.settingspqdb/hdr
content://com.mediatek.tv.settingspqdb/source
content://com.mediatek.tv.settingspqdb/stream
content://com.mediatek.tv.settingspqdb/gamemode
content://com.mediatek.tv.settingspqdb/videoInfo
content://com.mediatek.tv.settingspqdb/reset
```

Direct shell access is blocked:

```text
requires com.mediatek.tv.agent.settingspqdb.permission.READ_DATA
or com.mediatek.tv.agent.settingspqdb.permission.WRITE_DATA
```

Interpretation: the original settings app likely updates PQ state through this
provider. A sideloaded helper will only use this path if the MediaTek permission
is grantable; otherwise we need direct `vendor.mediatek.hardware.pq.IPq/default`.

## Picture Mode Storage Model

`MiscKey.apk` contains `GamePictureModeEntity` with fields:

```text
source
hdrType
pqMode
isActive
brightness
contrast
saturation
sharpness
colorTemp
twoPointWBR
twoPointWBG
twoPointWBB
localContrast
memc
gamma
mpegNR
dlc
gamingMJC
```

Relevant methods/strings:

```text
setPictureModeIdx(), paras ePicMode =
setColorTempratureIdx(), paras colorTempIdx =
setColorTempIdx(), paras eColorTemp =
setPictureMode(), paras pictureMode =
getPictureModeJson(source, hdrType)
GamePQModeDao.queryPictureMode(source, hdrType, pqMode)
GamePQModeDao.updatePictureMode(...)
```

Interpretation: HDR picture mode is tied to source + hdrType + pqMode rows and
per-stream JSON/PQ parameters, not just a single global integer.

## Native PQ Stack

Native strings confirm:

```text
vendor.mediatek.hardware.pq.IPq/default
vendor.mediatek.hardware.pq.IPq
PQ_AIDL
AServiceManager_waitForService
MI_PQ_SetHdrType
MI_PQ_GetHdrType
MI_PQ_ApplyParams_UpdateGlobalHDR
MI_PQ_ApplyParams_UpdatePerStreamHDR
MI_PQ_ApplyParams_SetRepoAllPkgByHdr
MI_PQ_ApplyParams_GetRepoWinParamsByHdr
MI_PQ_SetAIPQEnable
MI_PQRM_MEMC_Get_Table_Info
MI_PQRM_MEMC_Get_MJC_Effect_Info
```

`libPqService.so` exposes JNI methods:

```text
PqService_aipqEnable_native
PqService_aipqSetStr_native
PqService_aipqSupported_native
```

## Confirmed MediaTek IPq Binder Access

Direct Binder access to `vendor.mediatek.hardware.pq.IPq/default` works from
ADB shell for at least read calls.

Confirmed transaction:

```text
0x3b / 59 = getHdrType(int pqId, out return[], out hdrType[])
```

Observed live values:

```text
PQ id 0..3 -> status=0, return_code=0, hdr_type=0
PQ id 4..8 -> status=0, return_code=3, hdr_type=0
```

Interpretation: the higher PQ ids are accepted differently by the native service
than ids `0..3`, but the raw `getHdrType` call does not yet expose the visible
HDR10 picture profile. This still fits the earlier failed bridge tests: they
were aimed at XGIMI/legacy methods, while the visible HDR10 picture profile is
likely managed by the MediaTek PQ stream/repository layer.

High-value write candidates recovered from the NDK AIDL stub:

```text
0x8a / 138 = setHdrType(int pqId, EN_PQ_HDR_TYPE hdrType, out return)
0x9f / 159 = setPqParams(int pqId, string params, out return)
0xa0 / 160 = setPqParamsByGlobal(string params, out return)
0xa1 / 161 = setPqParamsByID(int id, string params, out return)
0xa4 / 164 = setPqRepositoryById(int streamId, bool enable, string params, out return)
0xa5 / 165 = setPqRepositoryByPkg(string package, bool enable, string params, out return)
```

### Native PQ Status JSON

`getGlobalNonAwarePqSetting` is transaction `0x36` / `54` and returns a live
UTF-16 JSON string from the MediaTek PQ stack.

Reproducible command:

```bash
scripts/xgimi_h20_adb.py -s 192.168.0.223:5555 pq-get-global-settings
```

Live result on the powered projector:

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

This is the first confirmed native status path for the visible picture pipeline.
It is now exposed in the Home Assistant integration through
`xgimi_control_bridge.get_native_pq_status` and native PQ sensors.

Write attempts with minimal JSON patches currently return `return_code=3`:

```text
setPqParamsByGlobal({"Backlight":"50"}) -> return_code=3
setPqParams(0, {"Brightness":"50"}) -> return_code=3
```

Interpretation: read access is solved. Write access likely needs the exact
repository/target payload shape used by the MediaTek settings app, not a minimal
single-key JSON patch.

## MediaTek OSD API Layer

`TvAgentService.apk` contains a higher-level Java AIDL wrapper that matches the
way the Google TV picture OSD updates picture settings:

```text
com.mediatek.extservice.IPqService
descriptor: com.mediatek.extservice.IPqService
service package: com.mediatek.extservice
bind action: PqService.remote
```

`TvVideoManager.createPqBinder()` binds that service and converts the returned
`IBinder` with `IPqService.Stub.asInterface(...)`.

Recovered OSD path:

```text
SourcePerstreamManager.updateToPqServiceBySource()
  -> SourceBaseJson.getJsonStringBySource()
  -> PackageUtils.getPackageName()
  -> TvVideoManager.setPqRepositoryByPkg()
  -> IPqService.setPqRepositoryByPkg()
```

This explains why the Google TV dashboard can change picture settings while the
XGIMI wrapper calls do not affect the visible HDR10 pipeline. The OSD uses a
privileged MediaTek repository API with full source/package-targeted JSON.

Live package inspection confirms that `PqService.remote` is protected by:

```text
com.mediatek.tv.extservice.permission.USE_PQSERVICE
protectionLevel: signature|privileged
```

The bridge `GET_EXT_PQ_SETTINGS` probe therefore fails on a normal sideloaded
install with:

```text
SecurityException: Not allowed to bind to service Intent { act=PqService.remote pkg=com.mediatek.extservice }
```

Interpretation: this is the OSD API, but it is only directly usable from
MediaTek/XGIMI-signed or privileged/system apps. For a normal Home Assistant
install we still need either the lower-level `vendor.mediatek.hardware.pq.IPq`
path with the full repository JSON payload or a privileged deployment path.

See `docs/extservice_ipq.md` for the Java AIDL transaction map and the next
bridge implementation target.

## Picture JSON Profile Model

`GmTvManager.getPictureModeJson(int ePicMode, int reserved)` returns
`RspPictureModeJson(retCode, jsonText)`.

The bridge app now exposes this as action
`de.drapple.xgimi.GET_PICTURE_JSON`, but live scans over modes `0..10,30,31`
and reserved values `0..4` returned `ret_code=0` with empty `json_text`.
This confirms the XGIMI wrapper method is not the active HDR10 profile source on
the tested firmware state.

The firmware default JSON has two important sections:

```text
perstream: Brightness, Contrast, Hue, MJC_Effect, AI_PQ, AISR,
           Local_Contrast, Gaming_MJC_Lvl, MJC_Deblur, MJC_Dejudder
global:    Backlight, Gamma, Color_Temperature, xgimiColorTemp,
           Live_Tone, Dark_Detail, Global_Dimming, Saturation
```

This is the first concrete native profile model that can cover brightness,
MEMC, AI picture, gamma, and color temperature without DPAD/menu automation.
