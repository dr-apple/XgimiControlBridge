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

Confirmed service:

```text
vendor.mediatek.hardware.pq.IPq/default
```

Confirmed descriptors/types in `vendor.mediatek.hardware.pq-V1-ndk.so`:

```text
vendor.mediatek.hardware.pq.IPq
vendor.mediatek.hardware.pq.PqConfig
vendor.mediatek.hardware.pq.PqInfo
vendor.mediatek.hardware.pq.PqTable
vendor.mediatek.hardware.pq.PQparam
vendor.mediatek.hardware.pq.ST_PQSETTING_INFO
vendor.mediatek.hardware.pq.ST_INPUT_VIDEO_FORMAT
vendor.mediatek.hardware.pq.ST_OUTPUT_VIDEO_FORMAT
vendor.mediatek.hardware.pq.ST_HDRMetadata
vendor.mediatek.hardware.pq.ST_HSY_ACTOR_INPUT
vendor.mediatek.hardware.pq.ST_HSY_ACTOR_OUTPUT
vendor.mediatek.hardware.pq.ReportPqUIStatus
vendor.mediatek.hardware.pq.ReportFormatInfo
vendor.mediatek.hardware.pq.ExecuteTable
vendor.mediatek.hardware.pq.PreferTable
```

Permission barrier:

```text
content://com.mediatek.tv.settingspqdb/*
requires com.mediatek.tv.agent.settingspqdb.permission.READ_DATA
or com.mediatek.tv.agent.settingspqdb.permission.WRITE_DATA
```

Practical options:

1. Reconstruct `IPq` AIDL calls and call binder directly.
2. Build a helper APK that declares MediaTek permissions and test whether they are
   normal, privileged, or signature-only.
3. If signature-only, use direct binder or a system/privileged install path.
