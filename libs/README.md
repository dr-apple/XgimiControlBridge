# Native Library Inputs

Place locally extracted native libraries here. They are intentionally ignored by Git.

Known relevant libraries:

- `xgimi.hardware.gmpf-V1-ndk.so`
- `vendor.mediatek.hardware.pq-V1-ndk.so`
- `vendor.mediatek.hardware.pq-impl.so`

Suggested extraction:

```bash
adb pull /vendor/lib64/ libs/vendor-lib64
adb pull /system_ext/lib64/ libs/system-ext-lib64
```

Then copy only the relevant `.so` files into this folder or pass the original paths
to the scripts in `scripts/`.
