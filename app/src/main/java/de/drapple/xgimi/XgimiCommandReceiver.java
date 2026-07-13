package de.drapple.xgimi;

import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.os.IBinder;
import android.os.Bundle;
import android.os.Parcel;
import android.util.Log;

import org.json.JSONObject;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/**
 * Small bridge between ADB/Home Assistant broadcasts and XGIMI's private GmTvManager API.
 *
 * No XGIMI classes are linked at build time. Everything is accessed through reflection,
 * because com.xgimi.api.jar on the projector contains DEX rather than normal JVM classes.
 */
public final class XgimiCommandReceiver extends BroadcastReceiver {
    private static final String TAG = "XgimiControlBridge";
    private static final String MANAGER_CLASS = "com.xgimi.gmpf.api.GmTvManager";
    private static final String VIDEO_MANAGER_CLASS = "com.xgimi.video.MstPictureManager";
    private static final String EXT_PQ_ACTION = "PqService.remote";
    private static final String EXT_PQ_PACKAGE = "com.mediatek.extservice";
    private static final String EXT_PQ_DESCRIPTOR = "com.mediatek.extservice.IPqService";
    private static final int EXT_PQ_GET_GLOBAL_SETTINGS = 17;
    private static final long EXT_PQ_BIND_TIMEOUT_MS = 2500;
    private static final String MIDDLEWARE_ACTION = "com.xgimi.misckey.GTV_MIDDLEWARE_SERVICE";
    private static final String MIDDLEWARE_PACKAGE = "com.xgimi.misckey";
    private static final String MIDDLEWARE_DESCRIPTOR =
            "com.xgimi.misckey.mw.IGtvMiddlewareInterface";
    private static final int MIDDLEWARE_EXECUTE_SYNC = 2;
    private static final String PQ_SERVICE_NAME = "vendor.mediatek.hardware.pq.IPq/default";
    private static final String PQ_DESCRIPTOR = "vendor.mediatek.hardware.pq.IPq";
    private static final int PQ_SET_MODE_TRANSACTION = 146;
    private static String lastParcelBackend = "unknown";

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
            if ("de.drapple.xgimi.GET_EXT_PQ_SETTINGS".equals(action)) {
                ExtPqSettingsResult result = readExtPqSettings(context);

                JSONObject json = new JSONObject();
                json.put("ok", true);
                json.put("command", "ext_pq_settings");
                json.put("backend", "mediatek_extservice_ipq");
                json.put("json_length", result.jsonText.length());
                json.put("json_text", result.jsonText);

                setResultCode(1);
                setResultData(json.toString());
                Log.i(TAG, json.toString());
                return;
            }

            if ("de.drapple.xgimi.MIDDLEWARE_EXEC_SYNC".equals(action)) {
                String type = getStringExtra(intent, "type", "");
                String command = getStringExtra(intent, "command", "");
                String payload = getStringExtra(intent, "payload", "");
                MiddlewareResult result = executeMiddlewareSync(this, context, type, command, payload);

                JSONObject json = new JSONObject();
                json.put("ok", true);
                json.put("command", "middleware_exec_sync");
                json.put("type", type);
                json.put("middleware_command", command);
                json.put("payload", payload);
                json.put("result", result.resultText);

                setResultCode(1);
                setResultData(json.toString());
                Log.i(TAG, json.toString());
                return;
            }

            if ("de.drapple.xgimi.PQ_SET_MODE".equals(action)) {
                int pqId = intent.getIntExtra("pq_id", 0);
                int displayModeType = intent.getIntExtra("display_mode_type", 0);
                int inputSourceType = intent.getIntExtra("input_source_type", 0);
                int outputVideoFormat = intent.getIntExtra("output_video_format", 0);
                boolean lowLatency = intent.getBooleanExtra("low_latency", false);
                int field4 = intent.getIntExtra("field4", 0);
                int field5 = intent.getIntExtra("field5", 0);
                int returnCode = setPqMode(
                        pqId,
                        displayModeType,
                        inputSourceType,
                        outputVideoFormat,
                        lowLatency,
                        field4,
                        field5
                );

                JSONObject json = new JSONObject();
                json.put("ok", true);
                json.put("command", "pq_set_mode");
                json.put("pq_id", pqId);
                json.put("display_mode_type", displayModeType);
                json.put("input_source_type", inputSourceType);
                json.put("output_video_format", outputVideoFormat);
                json.put("low_latency", lowLatency);
                json.put("field4", field4);
                json.put("field5", field5);
                json.put("return_code", returnCode);
                json.put("parcel_backend", lastParcelBackend);

                setResultCode(1);
                setResultData(json.toString());
                Log.i(TAG, json.toString());
                return;
            }

            Class<?> cls = Class.forName(MANAGER_CLASS);
            Object manager = cls.getMethod("getInstance").invoke(null);
            int source = intent.hasExtra("source")
                    ? intent.getIntExtra("source", 0)
                    : invokeInt(cls, manager, "getCurrentInputSource");

            if ("de.drapple.xgimi.SET_PICTURE_MODE".equals(action)) {
                int mode = resolveValue(intent, cls, PICTURE_FIELDS, "mode");
                CommandResult result = setPictureMode(cls, manager, source, mode);
                success("picture_mode", source, mode, result);
                return;
            }

            if ("de.drapple.xgimi.SET_MEMC".equals(action)) {
                int level = resolveValue(intent, cls, MEMC_FIELDS, "level");
                CommandResult result = setMemcLevel(cls, manager, source, level);
                success("memc", source, level, result);
                return;
            }

            if ("de.drapple.xgimi.GET_STATUS".equals(action)) {
                StatusResult status = readStatus(cls, manager, source);

                JSONObject json = new JSONObject();
                json.put("ok", true);
                json.put("source", source);
                json.put("picture_mode", status.pictureMode);
                json.put("memc", status.memcLevel);
                json.put("backend", status.backend);

                setResultCode(1);
                setResultData(json.toString());
                Log.i(TAG, json.toString());
                return;
            }

            if ("de.drapple.xgimi.GET_PICTURE_JSON".equals(action)) {
                int mode = intent.hasExtra("mode_value")
                        ? intent.getIntExtra("mode_value", 0)
                        : intent.getIntExtra("mode", 0);
                int reserved = intent.getIntExtra("reserved", 0);
                PictureJsonResult result = readPictureJson(cls, manager, mode, reserved);

                JSONObject json = new JSONObject();
                json.put("ok", true);
                json.put("command", "picture_json");
                json.put("mode", mode);
                json.put("reserved", reserved);
                json.put("ret_code", result.retCode);
                json.put("json_length", result.jsonText == null ? 0 : result.jsonText.length());
                json.put("json_text", result.jsonText == null ? "" : result.jsonText);

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

    private static CommandResult setPictureMode(Class<?> cls, Object manager, int source, int mode)
            throws Exception {
        Object primary = cls.getMethod("setPictureMode", int.class, int.class)
                .invoke(manager, source, mode);
        if (isTruthy(primary)) {
            return new CommandResult(primary, "gm_tv_manager_source");
        }

        Object videoManager = getVideoManager();
        Object fallback = videoManager.getClass().getMethod("setPictureMode", int.class)
                .invoke(videoManager, mode);
        return new CommandResult(fallback, "mst_picture_manager");
    }

    private static CommandResult setMemcLevel(Class<?> cls, Object manager, int source, int level)
            throws Exception {
        Object primary = cls.getMethod("setMemcLevel", int.class, int.class)
                .invoke(manager, source, level);
        if (isTruthy(primary)) {
            return new CommandResult(primary, "gm_tv_manager_source");
        }

        Object videoManager = getVideoManager();
        Object fallback = videoManager.getClass().getMethod("setMfcLevel", int.class)
                .invoke(videoManager, level);
        return new CommandResult(fallback == null ? "void" : fallback, "mst_picture_manager");
    }

    private static StatusResult readStatus(Class<?> cls, Object manager, int source) throws Exception {
        int picture = invokeInt(cls, manager, "getPictureMode", source);
        int memc = invokeInt(cls, manager, "getMemcLevel", source);
        String backend = "gm_tv_manager_source";

        try {
            Object videoManager = getVideoManager();
            int videoPicture = invokeInt(videoManager.getClass(), videoManager, "getPictureMode");
            int videoMemc = invokeInt(videoManager.getClass(), videoManager, "getMfcLevel");

            // The source-aware API can return default values even when the active video service differs.
            if (picture == 0 && memc == 0 && (videoPicture != 0 || videoMemc != 0)) {
                picture = videoPicture;
                memc = videoMemc;
                backend = "mst_picture_manager";
            }
        } catch (Throwable error) {
            Log.w(TAG, "MstPictureManager status fallback failed: " + error);
        }

        return new StatusResult(picture, memc, backend);
    }

    private static PictureJsonResult readPictureJson(Class<?> cls, Object manager, int mode, int reserved)
            throws Exception {
        Object response = cls.getMethod("getPictureModeJson", int.class, int.class)
                .invoke(manager, mode, reserved);
        int retCode = readIntMember(response, "getRetCode", "retCode");
        String jsonText = readStringMember(response, "getJsonText", "jsonText");
        return new PictureJsonResult(retCode, jsonText);
    }

    private static ExtPqSettingsResult readExtPqSettings(Context context) throws Exception {
        Context appContext = context.getApplicationContext();
        Intent serviceIntent = new Intent()
                .setAction(EXT_PQ_ACTION)
                .setPackage(EXT_PQ_PACKAGE);
        final CountDownLatch connected = new CountDownLatch(1);
        final IBinder[] binderRef = new IBinder[1];
        final String[] disconnectReason = new String[1];

        ServiceConnection connection = new ServiceConnection() {
            @Override
            public void onServiceConnected(ComponentName name, IBinder service) {
                binderRef[0] = service;
                connected.countDown();
            }

            @Override
            public void onServiceDisconnected(ComponentName name) {
                disconnectReason[0] = "Service disconnected: " + name;
            }

            @Override
            public void onBindingDied(ComponentName name) {
                disconnectReason[0] = "Binding died: " + name;
                connected.countDown();
            }

            @Override
            public void onNullBinding(ComponentName name) {
                disconnectReason[0] = "Null binding: " + name;
                connected.countDown();
            }
        };

        boolean bound = appContext.bindService(serviceIntent, connection, Context.BIND_AUTO_CREATE);
        if (!bound) {
            throw new IllegalStateException("Could not bind " + EXT_PQ_PACKAGE + "/" + EXT_PQ_ACTION);
        }

        try {
            if (!connected.await(EXT_PQ_BIND_TIMEOUT_MS, TimeUnit.MILLISECONDS)) {
                throw new IllegalStateException("Timed out binding " + EXT_PQ_PACKAGE + "/" + EXT_PQ_ACTION);
            }

            IBinder binder = binderRef[0];
            if (binder == null) {
                throw new IllegalStateException(disconnectReason[0] == null
                        ? "Service returned no binder"
                        : disconnectReason[0]);
            }

            Parcel data = Parcel.obtain();
            Parcel reply = Parcel.obtain();
            try {
                data.writeInterfaceToken(EXT_PQ_DESCRIPTOR);
                boolean transactOk = binder.transact(EXT_PQ_GET_GLOBAL_SETTINGS, data, reply, 0);
                if (!transactOk) {
                    throw new IllegalStateException("IPqService transaction failed");
                }
                reply.readException();
                String jsonText = reply.readString();
                return new ExtPqSettingsResult(jsonText == null ? "" : jsonText);
            } finally {
                reply.recycle();
                data.recycle();
            }
        } finally {
            appContext.unbindService(connection);
        }
    }

    private static MiddlewareResult executeMiddlewareSync(
            BroadcastReceiver receiver,
            Context context,
            String type,
            String command,
            String payload
    ) throws Exception {
        if (command == null || command.trim().isEmpty()) {
            throw new IllegalArgumentException("Missing --es command NAME");
        }

        Intent serviceIntent = new Intent()
                .setAction(MIDDLEWARE_ACTION)
                .setPackage(MIDDLEWARE_PACKAGE);
        IBinder binder = receiver.peekService(context, serviceIntent);
        if (binder == null) {
            throw new IllegalStateException("GtvMiddleware binder is not available via peekService");
        }

        Parcel data = obtainParcelForBinder(binder);
        Parcel reply = Parcel.obtain();
        try {
            data.writeInterfaceToken(MIDDLEWARE_DESCRIPTOR);
            data.writeString(type == null ? "" : type);
            data.writeString(command);
            data.writeString(payload == null ? "" : payload);
            boolean transactOk = binder.transact(MIDDLEWARE_EXECUTE_SYNC, data, reply, 0);
            if (!transactOk) {
                throw new IllegalStateException("GtvMiddleware executeSync transaction failed");
            }
            reply.readException();
            String resultText = reply.readString();
            return new MiddlewareResult(resultText == null ? "" : resultText);
        } finally {
            reply.recycle();
            data.recycle();
        }
    }

    private static int setPqMode(
            int pqId,
            int displayModeType,
            int inputSourceType,
            int outputVideoFormat,
            boolean lowLatency,
            int field4,
            int field5
    ) throws Exception {
        Class<?> serviceManager = Class.forName("android.os.ServiceManager");
        IBinder binder = (IBinder) serviceManager
                .getMethod("getService", String.class)
                .invoke(null, PQ_SERVICE_NAME);
        if (binder == null) {
            throw new IllegalStateException("Could not get service " + PQ_SERVICE_NAME);
        }

        Parcel data = obtainParcelForBinder(binder);
        Parcel reply = Parcel.obtain();
        try {
            data.writeInterfaceToken(PQ_DESCRIPTOR);
            data.writeInt(pqId);

            int parcelableStart = data.dataPosition();
            data.writeInt(0);
            data.writeInt(displayModeType);
            data.writeInt(inputSourceType);
            data.writeInt(outputVideoFormat);
            data.writeBoolean(lowLatency);
            data.writeInt(field4);
            data.writeInt(field5);
            int parcelableEnd = data.dataPosition();
            data.setDataPosition(parcelableStart);
            data.writeInt(parcelableEnd - parcelableStart);
            data.setDataPosition(parcelableEnd);

            boolean transactOk = binder.transact(PQ_SET_MODE_TRANSACTION, data, reply, 0);
            if (!transactOk) {
                throw new IllegalStateException("IPq setMode transaction failed");
            }
            reply.readException();
            return reply.readInt();
        } finally {
            reply.recycle();
            data.recycle();
        }
    }

    private static Parcel obtainParcelForBinder(IBinder binder) {
        try {
            Parcel parcel = (Parcel) Parcel.class
                    .getMethod("obtain", IBinder.class)
                    .invoke(null, binder);
            lastParcelBackend = "Parcel.obtain(IBinder)";
            return parcel;
        } catch (Throwable ignored) {
            Parcel parcel = Parcel.obtain();
            try {
                Parcel.class
                        .getDeclaredMethod("markForBinder", IBinder.class)
                        .invoke(parcel, binder);
                lastParcelBackend = "Parcel.markForBinder(IBinder)";
            } catch (Throwable markError) {
                lastParcelBackend = "Parcel.obtain fallback: "
                        + markError.getClass().getSimpleName();
            }
            return parcel;
        }
    }

    private static Object getVideoManager() throws Exception {
        Class<?> videoClass = Class.forName(VIDEO_MANAGER_CLASS);
        return videoClass.getMethod("getInstance").invoke(null);
    }

    private static boolean isTruthy(Object result) {
        if (result instanceof Boolean) {
            return (Boolean) result;
        }
        if (result instanceof Number) {
            return ((Number) result).intValue() != 0;
        }
        return result != null;
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

    private static int readIntMember(Object target, String getter, String fieldName) throws Exception {
        try {
            return ((Number) target.getClass().getMethod(getter).invoke(target)).intValue();
        } catch (NoSuchMethodException ignored) {
            Field field = target.getClass().getField(fieldName);
            return field.getInt(target);
        }
    }

    private static String readStringMember(Object target, String getter, String fieldName) throws Exception {
        try {
            Object value = target.getClass().getMethod(getter).invoke(target);
            return value == null ? "" : String.valueOf(value);
        } catch (NoSuchMethodException ignored) {
            Field field = target.getClass().getField(fieldName);
            Object value = field.get(target);
            return value == null ? "" : String.valueOf(value);
        }
    }

    private static String getStringExtra(Intent intent, String name, String defaultValue) {
        String value = intent.getStringExtra(name);
        return value == null ? defaultValue : value;
    }

    private void success(String command, int source, int value, CommandResult result) {
        try {
            JSONObject json = new JSONObject();
            json.put("ok", true);
            json.put("command", command);
            json.put("source", source);
            json.put("value", value);
            json.put("vendor_result", String.valueOf(result.vendorResult));
            json.put("backend", result.backend);
            setResultCode(1);
            setResultData(json.toString());
            Log.i(TAG, json.toString());
        } catch (Exception ignored) {
            setResultCode(1);
        }
    }

    private void fail(String message, Throwable error) {
        String detail = error == null ? message : message + ": " + error;
        if (!"unknown".equals(lastParcelBackend)) {
            detail = detail + " parcel_backend=" + lastParcelBackend;
        }
        Log.e(TAG, detail, error);
        setResultCode(-1);
        setResultData(detail);
    }

    private static final class CommandResult {
        final Object vendorResult;
        final String backend;

        CommandResult(Object vendorResult, String backend) {
            this.vendorResult = vendorResult;
            this.backend = backend;
        }
    }

    private static final class StatusResult {
        final int pictureMode;
        final int memcLevel;
        final String backend;

        StatusResult(int pictureMode, int memcLevel, String backend) {
            this.pictureMode = pictureMode;
            this.memcLevel = memcLevel;
            this.backend = backend;
        }
    }

    private static final class PictureJsonResult {
        final int retCode;
        final String jsonText;

        PictureJsonResult(int retCode, String jsonText) {
            this.retCode = retCode;
            this.jsonText = jsonText;
        }
    }

    private static final class ExtPqSettingsResult {
        final String jsonText;

        ExtPqSettingsResult(String jsonText) {
            this.jsonText = jsonText;
        }
    }

    private static final class MiddlewareResult {
        final String resultText;

        MiddlewareResult(String resultText) {
            this.resultText = resultText;
        }
    }
}
