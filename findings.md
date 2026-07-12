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
