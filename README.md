# XGIMI Control Bridge

Kleine Android-App für XGIMI H20 / Android 14. Sie nimmt ADB-Broadcasts entgegen
und ruft über Reflection die private XGIMI-API `GmTvManager` auf.

## Bauen

Projekt in Android Studio öffnen und **Build > Build APK(s)** wählen.

Die APK liegt anschließend typischerweise hier:

```text
app/build/outputs/apk/debug/app-debug.apk
```

Installation:

```bash
adb install -r app-debug.apk
```

Die App hat absichtlich kein Launcher-Icon. Sie arbeitet nur als Broadcast-Receiver.

## Testbefehle

Bildprofil Film:

```bash
adb shell am broadcast -n de.drapple.xgimi/.XgimiCommandReceiver   -a de.drapple.xgimi.SET_PICTURE_MODE --es mode movie
```

Weitere Profile:

```text
bright, standard, soft, user, game, auto, pc, movie, natural, sports
```

MEMC:

```bash
adb shell am broadcast -n de.drapple.xgimi/.XgimiCommandReceiver   -a de.drapple.xgimi.SET_MEMC --es level high
```

MEMC-Werte:

```text
off, low, middle, high, bypass
```

Status abfragen:

```bash
adb shell am broadcast -n de.drapple.xgimi/.XgimiCommandReceiver   -a de.drapple.xgimi.GET_STATUS
```

Bestimmte Quelle erzwingen:

```bash
--ei source 0
```

Quellen laut XGIMI-API:

```text
0 = internes Google TV / MM
1 = HDMI 1
2 = HDMI 2
3 = HDMI 3
4 = HDMI 4
```

Direkte numerische Werte sind ebenfalls möglich:

```bash
adb shell am broadcast -n de.drapple.xgimi/.XgimiCommandReceiver   -a de.drapple.xgimi.SET_PICTURE_MODE --ei value 7
```

## Bekannte XGIMI-Werte

Bildprofile:

```text
0 bright
1 standard
2 soft
3 user
4 game
5 auto
6 pc
7 movie
8 natural
9 sports
```

MEMC:

```text
0 off
1 low
2 middle
3 high
4 bypass
```

## Home Assistant Custom Integration

### Installation mit HACS

1. HACS öffnen.
2. **Custom repositories** öffnen.
3. Repository hinzufügen:

   ```text
   https://github.com/dr-apple/XgimiControlBridge
   ```

4. Kategorie **Integration** auswählen.
5. **XGIMI Control Bridge** installieren.
6. Home Assistant neu starten.
7. In Home Assistant **Einstellungen > Geräte & Dienste > Integration hinzufügen**
   öffnen und **XGIMI Control Bridge** auswählen.
8. Die bestehende Android-TV-/ADB-`media_player`-Entity des Projektors auswählen.

### Manuelle Installation

Dieses Repository enthält zusätzlich eine Custom Integration unter:

```text
custom_components/xgimi_control_bridge
```

Manuelle Installation:

1. Den Ordner `custom_components/xgimi_control_bridge` nach Home Assistant in
   `/config/custom_components/xgimi_control_bridge` kopieren.
2. Home Assistant neu starten.
3. In Home Assistant **Einstellungen > Geräte & Dienste > Integration hinzufügen**
   öffnen und **XGIMI Control Bridge** auswählen.
4. Die bestehende Android-TV-/ADB-`media_player`-Entity des Projektors auswählen.

Die Integration legt zwei Select-Entities an:

```text
select.xgimi_control_bridge_picture_mode
select.xgimi_control_bridge_memc
```

Außerdem stehen Services zur Verfügung:

```text
xgimi_control_bridge.set_picture_mode
xgimi_control_bridge.set_memc
xgimi_control_bridge.get_status
```

Beispiel Service-Aufruf:

```yaml
action: xgimi_control_bridge.set_picture_mode
data:
  entity_id: media_player.xgimi_h20
  mode: movie
```

MEMC:

```yaml
action: xgimi_control_bridge.set_memc
data:
  entity_id: media_player.xgimi_h20
  level: high
```

Die Integration nutzt intern weiterhin die Android-TV-ADB-Aktion. Der äquivalente
Rohbefehl wäre:

```yaml
action: androidtv.adb_command
target:
  entity_id: media_player.xgimi_h20
data:
  command: >-
    am broadcast -n de.drapple.xgimi/.XgimiCommandReceiver
    -a de.drapple.xgimi.SET_PICTURE_MODE
    --es mode movie
```

Hinweis: Das ist eine experimentelle Bridge gegen eine nicht dokumentierte Hersteller-API.
Nach Firmware-Updates können Methodennamen oder Berechtigungen geändert sein.
