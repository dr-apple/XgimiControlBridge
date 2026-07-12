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
