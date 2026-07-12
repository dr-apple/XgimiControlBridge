#!/usr/bin/env bash
set -euo pipefail

adb shell service list | sed -n '/xgimi\|mediatek\|pq\|tv/Ip'
adb shell lshal 2>/dev/null | sed -n '/xgimi\|mediatek\|pq\|gmpf/Ip' || true
adb shell cmd package resolve-service --brief -a com.mediatek.tvagent.action.AIDL_SERVICE 2>/dev/null || true
