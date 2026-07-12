# Native API Map

This file tracks candidate direct firmware APIs. Only promote an entry to
`Confirmed` after it visibly changes device behavior and is repeatable.

## Confirmed

### Autofocus

```bash
adb shell service call xgimi.hardware.gmpf.IProjectorFocusManager/default 3 i32 2
```

Python harness:

```bash
scripts/xgimi_h20_adb.py autofocus
```

Status: confirmed working.

## Candidate: XGIMI Video API

Source: `/system_ext/framework/com.xgimi.api.jar`

Important classes:

- `com.xgimi.aidl.IGimiVideo`
- `com.xgimi.video.MstPictureManager`
- `com.xgimi.gmpf.api.GmTvManager`
- `com.xgimi.gmpf.api.DisplayManager`
- `xgimi.hardware.gmpf.ProjectorFocusManagerService`

Relevant `IGimiVideo` methods:

```text
getPictureMode()I
setPictureMode(I)Z
getMfcLevel()I
setMfcLevel(I)V
setColorTemp(I)Z
setHdrEnable(Z)Z
setZoomMode(I)Z
setPictureItem(II)Z
resetPictureMode(IZ)V
```

Status: methods exist, but the first bridge tests did not visibly change HDR10
picture mode. Treat this as a non-HDR or inactive-pipeline candidate until proven.

## Candidate: XGIMI Display/Keystone/Zoom API

Source: `/system_ext/framework/com.xgimi.api.jar`

Relevant `DisplayManager` methods seen in dexdump:

```text
correctKeystone(...)
correctKeystoneEx(...)
correctKeystoneReset(...)
getCurrentKeystoneMode()
GetCurrentZoomLimitStep(...)
getCurrentZoomStep(...)
setDigitalZoomStep(I)I
setOpticalZoomStep(I)I
SetOpticalZoomLimitStep(I)I
getScreenZoomfactor()B
```

Status: candidate. Needs safe probe mapping before Home Assistant exposure.

## Candidate: MediaTek PQ

Strong log lead:

```text
GM_DISP_SCENE_V3::setPictureMode()
ePicMode=7->0
ePicMode=0->7
Hdr HDR10
mHdrType=HDR10
```

Likely runtime path:

```text
com.mediatek.tv.settings
-> PqModeManager
-> JNI
-> vendor.mediatek.hardware.pq-impl.so
-> GM_DISP_SCENE_V3
```

Status: highest-priority path for HDR picture mode, MEMC, color temperature,
gamma, brightness, and AI picture.
