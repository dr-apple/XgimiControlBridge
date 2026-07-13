# MediaTek ExtService IPqService

The Google TV picture OSD does not appear to call the XGIMI API directly for
HDR10 picture profiles. `TvAgentService.apk` contains a higher-level Java AIDL
wrapper around the native MediaTek PQ stack:

```text
com.mediatek.extservice.IPqService
descriptor: com.mediatek.extservice.IPqService
service package: com.mediatek.extservice
bind action: PqService.remote
```

`TvVideoManager.createPqBinder()` builds this intent:

```text
Intent()
  .setAction("PqService.remote")
  .setPackage("com.mediatek.extservice")
```

and converts the returned binder with:

```text
IPqService.Stub.asInterface(IBinder)
```

This is the likely "simple API" used by MediaTek/Google TV settings. It is
still a privileged vendor service, but it avoids raw NDK AIDL parcel work when
called from an app that can bind to `com.mediatek.extservice`.

Live package inspection confirms the privilege boundary:

```text
PqService.remote:
  com.mediatek.extservice/.PqService
  permission com.mediatek.tv.extservice.permission.USE_PQSERVICE

Permission:
  com.mediatek.tv.extservice.permission.USE_PQSERVICE
  protectionLevel: signature|privileged
```

A sideloaded APK cannot receive this permission. The read-only bridge probe
therefore fails as expected on a normal install:

```text
SecurityException: Not allowed to bind to service
Intent { act=PqService.remote pkg=com.mediatek.extservice }
```

## OSD Picture Path

The static path recovered from `TvAgentService.apk` is:

```text
SourcePerstreamManager.updateToPqServiceBySource(source, enable)
  -> SourceBaseJson.getJsonStringBySource(source, isIMaxAuto, isFmmUpdate)
  -> PackageUtils.getPackageName(context, source)
  -> TvVideoManager.setPqRepositoryByPkg(packageName, enable, json)
  -> IPqService.setPqRepositoryByPkg(packageName, enable, json)
  -> MediaTek PQ / GM_DISP_SCENE_V3
```

Supported source keys in the updater:

```text
mm, dtv, hdmi1, hdmi2, hdmi3, hdmi4, atv, component, composite
```

`PackageUtils.getPackageName()` builds package targets such as:

```text
mm     -> com.mediatek.wwtv.mediaplayer_[src:<id>, dev:<id>]
dtv    -> com.mediatek.tv.oneworld.tvcenter_[src:<id>, dev:<id>]
atv    -> com.google.android.tv.inputplayer_[src:<id>, dev:<id>]
other  -> com.cltv.hybrid_[src:<id>, dev:<id>] unless CLTV is enabled
```

For HDMI, the source id and device id are derived from MediaTek enum values
(`E_RENDER_WIN_INPUT_SOURCE_TYPE_HDMI` and `E_RENDER_SOURCE_DEVICE_TYPE_HDMI_PORT*`).

## High-Value Java AIDL Methods

```text
getGlobalPqSettings(): String
getGlobalRange(String): String
getPerstreamRange(String): String
getPresetGlobalPqParams(String): String
getPresetPerstreamPqParams(String): String
getGlobalPqHWParams(String): String
setPqParams(String): PQReturnVal
setPqParamsByGlobal(String): PQReturnVal
setPqParamsByTarget(String target, String json): PQReturnVal
setPqRepositoryById(int id, boolean enable, String json): PQReturnVal
setPqRepositoryByPkg(String packageName, boolean enable, String json): PQReturnVal
setPqHWParamsByGlobal(String): PQReturnVal
setPQNonLinear(String): PQReturnVal
aipqSetStr(boolean): PQReturnVal
aipqEnable(int, int, int): PQReturnVal
```

## Java Binder Transactions

These transaction ids are from `IPqService$Stub` in `TvAgentService.apk`:

```text
1   open
2   close
3   doPQ
6   setPqParamsByTarget
7   setPQNonLinear
8   getPQNonLinear
12  setPqParams
13  getPresetPerstreamPqParams
14  getPresetGlobalPqParams
15  getPerstreamRange
16  getGlobalRange
17  getGlobalPqSettings
20  setPqParamsByGlobal
23  setHdrColorInfo
24  bypassPerstreamPq
25  openSession
27  aipqSetStr
28  setPqRepositoryById
29  setPqRepositoryByPkg
30  setPqHWParamsByGlobal
31  getGlobalPqHWParams
33  aipqSupported
46  aipqEnable
```

The Java AIDL transaction numbers are not the same as the lower-level
`vendor.mediatek.hardware.pq.IPq/default` NDK AIDL transaction numbers. The Java
service is a wrapper that eventually reaches the same native PQ engine.

## Next Implementation Target

Bridge version `0.1.7` adds the first read-only probe for this layer:

```bash
adb shell am broadcast -n de.drapple.xgimi/.XgimiCommandReceiver \
  -a de.drapple.xgimi.GET_EXT_PQ_SETTINGS
```

or through the repo helper:

```bash
scripts/xgimi_h20_adb.py -s 192.168.0.223:5555 bridge-get-ext-pq-settings
```

It tries to bind to `com.mediatek.extservice` with `PqService.remote` and
performs Java Binder transaction `17` (`getGlobalPqSettings`) using raw
`Parcel` transact calls. On a normal sideloaded install this confirms the
`signature|privileged` permission block above.

If the bridge is ever run as a privileged/system app, test write calls in this
order:

```text
setPqRepositoryByPkg(packageName, true, fullProfileJson)
setPqParamsByTarget(target, fullProfileJson)
setPqParamsByGlobal(fullGlobalJson)
```

The key difference from the failed raw native writes is that the OSD path sends
full repository JSON and a package/source target, not a one-key patch like
`{"Brightness":"50"}`.
