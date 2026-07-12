# APK Inputs

Place locally extracted APKs here. They are intentionally ignored by Git because this
repository is public and the files are proprietary firmware/application artifacts.

Known relevant APKs:

- `XRMService.apk`
- `XgimiTvSettingsVendor.apk`
- `TvAgentService.apk`
- `MiscKey.apk`
- MediaTek TV settings APKs, if present on the device

Suggested extraction:

```bash
adb shell pm path com.mediatek.tv.settings
adb shell pm path com.mediatek.tv.agent
adb pull /path/from/pm/path.apk apks/
```
