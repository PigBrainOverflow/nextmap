#include "emap/utils.h"


namespace emap {

std::string ptr_to_hexstr(const void* ptr) {
    char buf[2 + sizeof(uintptr_t) * 2 + 1]; // "0x" + 16 hex digits + null
    std::snprintf(buf, sizeof(buf), "%p", ptr);
    return std::string(buf);
}

}