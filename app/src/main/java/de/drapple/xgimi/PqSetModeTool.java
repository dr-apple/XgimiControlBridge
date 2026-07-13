package de.drapple.xgimi;

import android.os.IBinder;
import android.os.Parcel;

public final class PqSetModeTool {
    private static final String PQ_SERVICE_NAME = "vendor.mediatek.hardware.pq.IPq/default";
    private static final String PQ_DESCRIPTOR = "vendor.mediatek.hardware.pq.IPq";
    private static final int PQ_SET_MODE_TRANSACTION = 146;

    private PqSetModeTool() {
    }

    public static void main(String[] args) throws Exception {
        try {
            System.load("/system/lib/libandroid_runtime.so");
        } catch (Throwable ignored) {
            // app_process loads this automatically; dalvikvm32 needs a best-effort nudge.
        }

        if (args.length < 7) {
            System.err.println("usage: PqSetModeTool pqId displayMode inputSource outputFormat lowLatency field4 field5");
            System.exit(2);
            return;
        }

        int pqId = Integer.parseInt(args[0]);
        int displayModeType = Integer.parseInt(args[1]);
        int inputSourceType = Integer.parseInt(args[2]);
        int outputVideoFormat = Integer.parseInt(args[3]);
        boolean lowLatency = Boolean.parseBoolean(args[4]);
        int field4 = Integer.parseInt(args[5]);
        int field5 = Integer.parseInt(args[6]);

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

            boolean ok = binder.transact(PQ_SET_MODE_TRANSACTION, data, reply, 0);
            if (!ok) {
                throw new IllegalStateException("IPq setMode transaction failed");
            }
            reply.readException();
            int returnCode = reply.readInt();
            System.out.println("return_code=" + returnCode);
        } finally {
            reply.recycle();
            data.recycle();
        }
    }

    private static Parcel obtainParcelForBinder(IBinder binder) {
        try {
            return (Parcel) Parcel.class
                    .getMethod("obtain", IBinder.class)
                    .invoke(null, binder);
        } catch (Throwable ignored) {
            Parcel parcel = Parcel.obtain();
            try {
                Parcel.class
                        .getDeclaredMethod("markForBinder", IBinder.class)
                        .invoke(parcel, binder);
            } catch (Throwable ignoredAgain) {
                // Older Android releases do not need binder-stability marking here.
            }
            return parcel;
        }
    }
}
