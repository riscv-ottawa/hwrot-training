// The second hop of the boot chain. ROM verifies ROM_EXT, ROM_EXT verifies
// this, and reaching test_main shows that both signatures checked out.
#include "sw/device/lib/runtime/log.h"
#include "sw/device/lib/testing/test_framework/ottf_main.h"

OTTF_DEFINE_TEST_CONFIG(.enable_concurrency = false,
                        .console.test_may_clobber = false, );
bool test_main(void) {
  LOG_INFO("owner_hello: the owner image is running");
  return true;
}
