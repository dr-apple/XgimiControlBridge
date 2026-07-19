#include <android/binder_ibinder.h>
#include <android/binder_parcel.h>
#include <android/binder_status.h>

#include <cstdlib>
#include <cstring>
#include <dlfcn.h>
#include <iostream>
#include <memory>
#include <string>

namespace {

constexpr const char* kPqService = "vendor.mediatek.hardware.pq.IPq/default";
constexpr const char* kPqDescriptor = "vendor.mediatek.hardware.pq.IPq";
constexpr uint32_t kGetHdrTypeTransaction = 59;
constexpr uint32_t kSetModeTransaction = 146;

struct BinderDeleter {
    void operator()(AIBinder* binder) const {
        if (binder != nullptr) {
            AIBinder_decStrong(binder);
        }
    }
};

struct ParcelDeleter {
    void operator()(AParcel* parcel) const {
        if (parcel != nullptr) {
            AParcel_delete(parcel);
        }
    }
};

struct StatusDeleter {
    void operator()(AStatus* status) const {
        if (status != nullptr) {
            AStatus_delete(status);
        }
    }
};

using BinderPtr = std::unique_ptr<AIBinder, BinderDeleter>;
using ParcelPtr = std::unique_ptr<AParcel, ParcelDeleter>;
using StatusPtr = std::unique_ptr<AStatus, StatusDeleter>;
using ServiceGetter = AIBinder* (*)(const char*);

void* onCreate(void*) {
    return nullptr;
}

void onDestroy(void*) {
}

binder_status_t onTransact(AIBinder*, transaction_code_t, const AParcel*, AParcel*) {
    return STATUS_UNKNOWN_TRANSACTION;
}

ServiceGetter loadServiceGetter(void* lib, const char* symbol) {
    void* raw = dlsym(lib, symbol);
    if (raw == nullptr) {
        return nullptr;
    }
    return reinterpret_cast<ServiceGetter>(raw);
}

int parseInt(const char* value, const char* name) {
    char* end = nullptr;
    long parsed = std::strtol(value, &end, 0);
    if (end == value || *end != '\0') {
        std::cerr << "Invalid integer for " << name << ": " << value << "\n";
        std::exit(2);
    }
    return static_cast<int>(parsed);
}

bool parseBool(const char* value) {
    return std::strcmp(value, "1") == 0
            || std::strcmp(value, "true") == 0
            || std::strcmp(value, "yes") == 0
            || std::strcmp(value, "on") == 0;
}

void requireOk(binder_status_t status, const char* operation) {
    if (status != STATUS_OK) {
        std::cerr << operation << " failed: binder_status=" << status << "\n";
        std::exit(1);
    }
}

BinderPtr getPqBinder() {
    void* binderNdk = dlopen("libbinder_ndk.so", RTLD_NOW);
    if (binderNdk == nullptr) {
        std::cerr << "Could not open libbinder_ndk.so: " << dlerror() << "\n";
        return nullptr;
    }

    ServiceGetter checkService = loadServiceGetter(binderNdk, "AServiceManager_checkService");
    ServiceGetter waitForService = loadServiceGetter(binderNdk, "AServiceManager_waitForService");
    if (checkService == nullptr && waitForService == nullptr) {
        std::cerr << "libbinder_ndk.so does not export AServiceManager service getters\n";
        return nullptr;
    }

    BinderPtr binder(checkService == nullptr ? nullptr : checkService(kPqService));
    if (!binder) {
        binder.reset(waitForService == nullptr ? nullptr : waitForService(kPqService));
    }
    if (!binder) {
        std::cerr << "Could not get service " << kPqService << "\n";
        return nullptr;
    }

    static AIBinder_Class* clazz = AIBinder_Class_define(
            kPqDescriptor,
            onCreate,
            onDestroy,
            onTransact);
    if (clazz == nullptr) {
        std::cerr << "Could not define binder class for " << kPqDescriptor << "\n";
        return nullptr;
    }
    if (!AIBinder_associateClass(binder.get(), clazz)) {
        std::cerr << "Could not associate binder class " << kPqDescriptor << "\n";
        return nullptr;
    }
    return binder;
}

int getHdrType(int pqId) {
    BinderPtr binder = getPqBinder();
    if (!binder) {
        return 1;
    }

    AParcel* rawIn = nullptr;
    requireOk(AIBinder_prepareTransaction(binder.get(), &rawIn), "AIBinder_prepareTransaction");
    ParcelPtr in(rawIn);

    requireOk(AParcel_writeInt32(in.get(), pqId), "write pqId");
    requireOk(AParcel_writeInt32(in.get(), 0), "write return array placeholder");
    requireOk(AParcel_writeInt32(in.get(), 0), "write hdr type array placeholder");
    AParcel* rawOut = nullptr;
    AParcel* rawInForTransact = in.release();
    binder_status_t transactStatus = AIBinder_transact(
            binder.get(),
            kGetHdrTypeTransaction,
            &rawInForTransact,
            &rawOut,
            0);
    ParcelPtr out(rawOut);
    if (rawInForTransact != nullptr) {
        AParcel_delete(rawInForTransact);
    }
    requireOk(transactStatus, "AIBinder_transact");

    AStatus* rawStatus = nullptr;
    requireOk(AParcel_readStatusHeader(out.get(), &rawStatus), "read status header");
    StatusPtr status(rawStatus);
    if (!AStatus_isOk(status.get())) {
        std::cerr << "Remote exception: "
                  << AStatus_getExceptionCode(status.get())
                  << " service_specific="
                  << AStatus_getServiceSpecificError(status.get())
                  << "\n";
        return 1;
    }

    int32_t statusArrayLength = 0;
    int32_t typeArrayLength = 0;
    int32_t returnCode = 0;
    int32_t hdrType = 0;
    requireOk(AParcel_readInt32(out.get(), &statusArrayLength), "read status array length");
    if (statusArrayLength > 0) {
        requireOk(AParcel_readInt32(out.get(), &returnCode), "read return code");
    }
    requireOk(AParcel_readInt32(out.get(), &typeArrayLength), "read type array length");
    if (typeArrayLength > 0) {
        requireOk(AParcel_readInt32(out.get(), &hdrType), "read hdr type");
    }
    std::cout << "return_code=" << returnCode << " hdr_type=" << hdrType << "\n";
    return 0;
}

int setMode(
        int pqId,
        int displayModeType,
        int inputSourceType,
        int outputVideoFormat,
        bool lowLatency,
        int field4,
        int field5) {
    BinderPtr binder = getPqBinder();
    if (!binder) {
        return 1;
    }

    AParcel* rawIn = nullptr;
    requireOk(AIBinder_prepareTransaction(binder.get(), &rawIn), "AIBinder_prepareTransaction");
    ParcelPtr in(rawIn);

    requireOk(AParcel_writeInt32(in.get(), pqId), "write pqId");

    int32_t parcelableStart = AParcel_getDataPosition(in.get());
    requireOk(AParcel_writeInt32(in.get(), 0), "write parcelable size placeholder");
    requireOk(AParcel_writeInt32(in.get(), displayModeType), "write displayModeType");
    requireOk(AParcel_writeInt32(in.get(), inputSourceType), "write inputSourceType");
    requireOk(AParcel_writeInt32(in.get(), outputVideoFormat), "write outputVideoFormat");
    requireOk(AParcel_writeBool(in.get(), lowLatency), "write lowLatency");
    requireOk(AParcel_writeInt32(in.get(), field4), "write field4");
    requireOk(AParcel_writeInt32(in.get(), field5), "write field5");
    int32_t parcelableEnd = AParcel_getDataPosition(in.get());

    requireOk(AParcel_setDataPosition(in.get(), parcelableStart), "seek parcelable start");
    requireOk(AParcel_writeInt32(in.get(), parcelableEnd - parcelableStart), "write parcelable size");
    requireOk(AParcel_setDataPosition(in.get(), parcelableEnd), "seek parcelable end");
    requireOk(AParcel_writeInt32(in.get(), 0), "write return placeholder");

    AParcel* rawOut = nullptr;
    AParcel* rawInForTransact = in.release();
    binder_status_t transactStatus = AIBinder_transact(
            binder.get(),
            kSetModeTransaction,
            &rawInForTransact,
            &rawOut,
            0);
    ParcelPtr out(rawOut);
    if (rawInForTransact != nullptr) {
        AParcel_delete(rawInForTransact);
    }
    requireOk(transactStatus, "AIBinder_transact");

    AStatus* rawStatus = nullptr;
    requireOk(AParcel_readStatusHeader(out.get(), &rawStatus), "read status header");
    StatusPtr status(rawStatus);
    if (!AStatus_isOk(status.get())) {
        std::cerr << "Remote exception: "
                  << AStatus_getExceptionCode(status.get())
                  << " service_specific="
                  << AStatus_getServiceSpecificError(status.get())
                  << "\n";
        return 1;
    }

    int32_t returnCode = 0;
    requireOk(AParcel_readInt32(out.get(), &returnCode), "read return code");
    std::cout << "return_code=" << returnCode << "\n";
    return 0;
}

void usage(const char* argv0) {
    std::cerr
            << "usage:\n"
            << "  " << argv0
            << " get-hdr-type [pqId]\n"
            << "  " << argv0
            << " set-mode [pqId displayModeType inputSourceType outputVideoFormat lowLatency field4 field5]\n";
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        usage(argv[0]);
        return 2;
    }

    if (std::strcmp(argv[1], "get-hdr-type") == 0) {
        int pqId = argc > 2 ? parseInt(argv[2], "pqId") : 0;
        return getHdrType(pqId);
    }

    if (std::strcmp(argv[1], "set-mode") != 0) {
        usage(argv[0]);
        return 2;
    }

    int pqId = argc > 2 ? parseInt(argv[2], "pqId") : 0;
    int displayModeType = argc > 3 ? parseInt(argv[3], "displayModeType") : 0;
    int inputSourceType = argc > 4 ? parseInt(argv[4], "inputSourceType") : 0;
    int outputVideoFormat = argc > 5 ? parseInt(argv[5], "outputVideoFormat") : 0;
    bool lowLatency = argc > 6 ? parseBool(argv[6]) : false;
    int field4 = argc > 7 ? parseInt(argv[7], "field4") : 0;
    int field5 = argc > 8 ? parseInt(argv[8], "field5") : 0;

    return setMode(
            pqId,
            displayModeType,
            inputSourceType,
            outputVideoFormat,
            lowLatency,
            field4,
            field5);
}
