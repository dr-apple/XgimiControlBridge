# Binder Notes

Confirmed HAL services on XGIMI H20 / Android 14:

```text
xgimi.hardware.gmpf.IProjectorFocusManager/default
xgimi.hardware.gmpf.IDisplayManager/default
xgimi.hardware.gmpf.IGmTvManager/default
xgimi.hardware.gmpf.IPowerManager/default
xgimi.hardware.gmpf.IGmAudioManager/default
xgimi.hardware.gmpf.IConfigManager/default
xgimi.hardware.gmpf.IDataBaseManager/default
```

Confirmed autofocus call:

```bash
adb shell service call xgimi.hardware.gmpf.IProjectorFocusManager/default 3 i32 2
```

This starts autofocus immediately, so the binder path is:

```text
ADB -> Binder -> IProjectorFocusManager -> hardware
```

Open questions:

- Which transaction IDs map to picture/HDR/MEMC/color/zoom/power?
- Is HDR picture mode handled by `IGmTvManager/default` or by MediaTek PQ?
- Does `vendor.mediatek.hardware.pq` expose a stable AIDL interface that can be
  called from shell or a small helper binary?
