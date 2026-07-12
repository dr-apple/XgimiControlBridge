# Framework Inputs

Place locally extracted framework/API jars here. They are intentionally ignored by Git.

Known relevant file:

- `/system_ext/framework/com.xgimi.api.jar`

Suggested extraction:

```bash
adb pull /system_ext/framework/com.xgimi.api.jar framework/
```

If `dexdump` is available, create a text dump for searching:

```bash
dexdump -d framework/com.xgimi.api.jar > framework/com.xgimi.api.dump
```
