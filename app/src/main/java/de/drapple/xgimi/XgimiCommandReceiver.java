package de.drapple.xgimi;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;

import org.json.JSONObject;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

/**
 * Small bridge between ADB/Home Assistant broadcasts and XGIMI's private GmTvManager API.
 *
 * No XGIMI classes are linked at build time. Everything is accessed through reflection,
 * because com.xgimi.api.jar on the projector contains DEX rather than normal JVM classes.
 */
public final class XgimiCommandReceiver extends BroadcastReceiver {
    private static final String TAG = "XgimiControlBridge";
    private static final String MANAGER_CLASS = "com.xgimi.gmpf.api.GmTvManager";

    private static final Map<String, String> PICTURE_FIELDS = new HashMap<>();
    private static final Map<String, String> MEMC_FIELDS = new HashMap<>();

    static {
        PICTURE_FIELDS.put("bright", "PICTURE_MODE_BRIGHT");
        PICTURE_FIELDS.put("standard", "PICTURE_MODE_STANTARD"); // typo exists in XGIMI API
        PICTURE_FIELDS.put("soft", "PICTURE_MODE_SOFT");
        PICTURE_FIELDS.put("user", "PICTURE_MODE_USER");
        PICTURE_FIELDS.put("game", "PICTURE_MODE_GAME");
        PICTURE_FIELDS.put("auto", "PICTURE_MODE_AUTO");
        PICTURE_FIELDS.put("pc", "PICTURE_MODE_PC");
        PICTURE_FIELDS.put("movie", "PICTURE_MODE_MOVIE");
        PICTURE_FIELDS.put("natural", "PICTURE_MODE_NATURAL");
        PICTURE_FIELDS.put("sports", "PICTURE_MODE_SPORTS");

        MEMC_FIELDS.put("off", "MEMC_OFF");
        MEMC_FIELDS.put("low", "MEMC_LEVEL_LOW");
        MEMC_FIELDS.put("middle", "MEMC_LEVEL_MIDDLE");
        MEMC_FIELDS.put("medium", "MEMC_LEVEL_MIDDLE");
        MEMC_FIELDS.put("high", "MEMC_LEVEL_HIGH");
        MEMC_FIELDS.put("bypass", "MEMC_BY_PASS");
    }

    @Override
    public void onReceive(Context context, Intent intent) {
        final String action = intent.getAction();
        try {
            Class<?> cls = Class.forName(MANAGER_CLASS);
            Object manager = cls.getMethod("getInstance").invoke(null);
            int source = intent.hasExtra("source")
                    ? intent.getIntExtra("source", 0)
                    : invokeInt(cls, manager, "getCurrentInputSource");

            if ("de.drapple.xgimi.SET_PICTURE_MODE".equals(action)) {
                int mode = resolveValue(intent, cls, PICTURE_FIELDS, "mode");
                Object result = cls.getMethod("setPictureMode", int.class, int.class)
                        .invoke(manager, source, mode);
                success("picture_mode", source, mode, result);
                return;
            }

            if ("de.drapple.xgimi.SET_MEMC".equals(action)) {
                int level = resolveValue(intent, cls, MEMC_FIELDS, "level");
                Object result = cls.getMethod("setMemcLevel", int.class, int.class)
                        .invoke(manager, source, level);
                success("memc", source, level, result);
                return;
            }

            if ("de.drapple.xgimi.GET_STATUS".equals(action)) {
                int picture = invokeInt(cls, manager, "getPictureMode", source);
                int memc = invokeInt(cls, manager, "getMemcLevel", source);

                JSONObject json = new JSONObject();
                json.put("ok", true);
                json.put("source", source);
                json.put("picture_mode", picture);
                json.put("memc", memc);

                setResultCode(1);
                setResultData(json.toString());
                Log.i(TAG, json.toString());
                return;
            }

            fail("Unknown action: " + action, null);
        } catch (Throwable error) {
            fail("Command failed", error);
        }
    }

    private static int resolveValue(
            Intent intent,
            Class<?> cls,
            Map<String, String> names,
            String extraName
    ) throws Exception {
        if (intent.hasExtra("value")) {
            return intent.getIntExtra("value", 0);
        }

        String raw = intent.getStringExtra(extraName);
        if (raw == null || raw.trim().isEmpty()) {
            throw new IllegalArgumentException(
                    "Missing --es " + extraName + " NAME or --ei value NUMBER"
            );
        }

        String normalized = raw.trim().toLowerCase(Locale.ROOT);
        String fieldName = names.get(normalized);
        if (fieldName == null) {
            throw new IllegalArgumentException(
                    "Unknown " + extraName + ": " + raw + ". Allowed: " + names.keySet()
            );
        }

        Field field = cls.getField(fieldName);
        return field.getInt(null);
    }

    private static int invokeInt(Class<?> cls, Object target, String method, Object... args)
            throws Exception {
        Class<?>[] types = new Class<?>[args.length];
        for (int i = 0; i < args.length; i++) {
            types[i] = int.class;
        }
        Method m = cls.getMethod(method, types);
        return ((Number) m.invoke(target, args)).intValue();
    }

    private void success(String command, int source, int value, Object vendorResult) {
        try {
            JSONObject json = new JSONObject();
            json.put("ok", true);
            json.put("command", command);
            json.put("source", source);
            json.put("value", value);
            json.put("vendor_result", String.valueOf(vendorResult));
            setResultCode(1);
            setResultData(json.toString());
            Log.i(TAG, json.toString());
        } catch (Exception ignored) {
            setResultCode(1);
        }
    }

    private void fail(String message, Throwable error) {
        String detail = error == null ? message : message + ": " + error;
        Log.e(TAG, detail, error);
        setResultCode(-1);
        setResultData(detail);
    }
}
