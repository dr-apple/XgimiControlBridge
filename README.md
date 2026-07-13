# XGIMI Control Bridge

Kleine Android-App für XGIMI H20 / Android 14. Sie nimmt ADB-Broadcasts entgegen
und ruft über Reflection die private XGIMI-API `GmTvManager` auf.

## Reverse Engineering Status

Dieses Projekt wird jetzt zusätzlich als Reverse-Engineering-Repo für native
XGIMI-H20-Steuerung geführt. Ziel ist eine Home-Assistant-Integration ohne
DPAD-/Menü-Automatisierung.

Neue Struktur:

```text
apks/          lokale, ignorierte APK-Inputs
framework/     lokale, ignorierte Framework-/DEX-Inputs
libs/          lokale, ignorierte native Libraries
binder/        Binder-Service-Notizen
docs/          Analyseplan und Native-API-Map
scripts/       reproduzierbare Scan- und ADB-Testwerkzeuge
findings.md    fortlaufende Erkenntnisse
homeassistant/ Zielbild für die native HA-Integration
```

Wichtig: Firmware-APKs, Framework-JARs und `.so`-Dateien werden absichtlich nicht
ins öffentliche Git-Repo aufgenommen. Sie bleiben lokal und werden von den Skripten
analysiert.

Bestätigt ist bisher der native Autofokus-Aufruf:

```bash
adb shell service call xgimi.hardware.gmpf.IProjectorFocusManager/default 3 i32 2
```

Die bisherigen Picture-/MEMC-Aufrufe über `GmTvManager` erreichen zwar die App,
ändern aber den sichtbaren HDR10-Bildmodus nicht zuverlässig. Der aktuell stärkste
Lead für HDR Picture Mode, MEMC, Color Temperature, Gamma, Brightness und AI Picture
ist daher die MediaTek-PQ-Pipeline:

```text
Settings -> PqModeManager -> JNI -> vendor.mediatek.hardware.pq-impl.so -> GM_DISP_SCENE_V3
```

Bestätigt ist inzwischen ein nativer MediaTek-PQ-Statusleser:

```bash
scripts/xgimi_h20_adb.py -s 192.168.0.223:5555 pq-get-global-settings
```

Dieser liest direkt Werte wie `Picture_Mode`, `Backlight`, `Brightness`,
`Gamma`, `Color_Temperature`, `AI_PQ`, `MJC_Effect` und `Local_Contrast`.
Schreibzugriffe über `setPqParams*` sind gefunden, benötigen aber noch das
exakte Firmware-Payload-Format.

Zusätzlich ist jetzt die OSD-nahe Java-Schicht gefunden: Google TV bindet
`com.mediatek.extservice` mit der Action `PqService.remote` und ruft
`com.mediatek.extservice.IPqService` auf. Besonders relevant ist
`setPqRepositoryByPkg(packageName, enable, json)`, weil dieser Pfad full-profile
JSON mit Source-/Paket-Ziel nutzt. Details stehen in `docs/extservice_ipq.md`.
Die Bridge `0.1.7` enthält dafür den ersten vorsichtigen Lesetest:
`de.drapple.xgimi.GET_EXT_PQ_SETTINGS`. Live getestet: der Dienst ist durch
`com.mediatek.tv.extservice.permission.USE_PQSERVICE` geschützt
(`signature|privileged`). Eine normal sideloaded APK kann ihn daher nicht direkt
binden; der Pfad bleibt als Diagnose und für mögliche privilegierte Installationen
dokumentiert.

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

Die Integration legt zwei klassische Select-Entities fuer die alte XGIMI-Bridge an:

```text
select.xgimi_control_bridge_picture_mode
select.xgimi_control_bridge_memc
```

Fuer die bestaetigte native MediaTek-PQ-Steuerung gibt es zusaetzlich echte
HA-Regler:

```text
number.xgimi_control_bridge_native_pq_backlight
number.xgimi_control_bridge_native_pq_brightness
number.xgimi_control_bridge_native_pq_contrast
```

Diese Regler schreiben direkt ueber `vendor.mediatek.hardware.pq.IPq/default`
und lesen den Status danach wieder zurueck. Auf deiner Anlage heissen sie je
nach gewaehlter Entity zum Beispiel:

```text
number.wohnzimmer_xgimi_control_bridge_native_pq_backlight
number.wohnzimmer_xgimi_control_bridge_native_pq_brightness
number.wohnzimmer_xgimi_control_bridge_native_pq_contrast
```

Die nativen Bildoptionen liegen als eigene Dropdowns daneben:

```text
select.wohnzimmer_xgimi_control_bridge_native_pq_picture_mode
select.wohnzimmer_xgimi_control_bridge_native_pq_gamma
select.wohnzimmer_xgimi_control_bridge_native_pq_color_temperature
select.wohnzimmer_xgimi_control_bridge_native_pq_ai_picture
select.wohnzimmer_xgimi_control_bridge_native_pq_memc
select.wohnzimmer_xgimi_control_bridge_native_pq_local_contrast
```

Wichtig: `select.xgimi_control_bridge_picture_mode` ist der alte XGIMI-Wrapper.
Fuer HDR10/IMAX und die sichtbare MediaTek-PQ-Pipeline ist der native
`select.*_native_pq_picture_mode` relevant.

Zusaetzlich gibt es Status-Sensoren und einen Button zum manuellen Aktualisieren:

```text
button.xgimi_control_bridge_refresh_status
button.xgimi_control_bridge_refresh_native_pq_status
sensor.xgimi_control_bridge_picture_mode
sensor.xgimi_control_bridge_memc
sensor.xgimi_control_bridge_source
sensor.xgimi_control_bridge_native_pq_backlight
sensor.xgimi_control_bridge_native_pq_brightness
sensor.xgimi_control_bridge_native_pq_contrast
sensor.xgimi_control_bridge_native_pq_gamma
sensor.xgimi_control_bridge_native_pq_color_temperature
sensor.xgimi_control_bridge_native_pq_ai_picture
sensor.xgimi_control_bridge_native_pq_memc
sensor.xgimi_control_bridge_native_pq_local_contrast
sensor.xgimi_control_bridge_native_pq_picture_mode
sensor.xgimi_control_bridge_last_command_ok
sensor.xgimi_control_bridge_last_adb_response
```

Der Status wird aus dem `adb_response`-Attribut der Android-TV-ADB-Entity gelesen.
Wenn Steuerung oder Status nicht funktionieren, zuerst den Button
**Refresh Native PQ Status** druecken und danach die nativen Sensoren pruefen.
Der Roh-ADB-Sensor wird absichtlich gekuerzt, damit Home Assistant keine zu grossen
Recorder-Attribute speichert.

Außerdem stehen Services zur Verfügung:

```text
xgimi_control_bridge.set_picture_mode
xgimi_control_bridge.set_memc
xgimi_control_bridge.get_status
xgimi_control_bridge.get_native_pq_status
xgimi_control_bridge.set_native_pq_value
xgimi_control_bridge.get_ext_pq_status
```

Beispiel Service-Aufruf:

```yaml
action: xgimi_control_bridge.set_picture_mode
target:
  entity_id: media_player.xgimi_h20
data:
  mode: movie
```

Nativer MediaTek-PQ-Status:

```yaml
action: xgimi_control_bridge.get_native_pq_status
target:
  entity_id: media_player.xgimi_h20
```

Nativer MediaTek-PQ-Schreibzugriff, live bestätigt mit Backlight 40 -> 41 -> 40:

```yaml
action: xgimi_control_bridge.set_native_pq_value
target:
  entity_id: media_player.xgimi_h20
data:
  key: Backlight
  value: 40
```

OSD-nahe ExtService-PQ-Schicht:

```yaml
action: xgimi_control_bridge.get_ext_pq_status
target:
  entity_id: media_player.xgimi_h20
```

MEMC:

```yaml
action: xgimi_control_bridge.set_memc
target:
  entity_id: media_player.xgimi_h20
data:
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
