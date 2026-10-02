with open('runtime/native/source/ArchitectNativeRuntime.c', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add probe definitions right before install_inventory_transfer_probe
probe_defs = '''
/* =========================================================================
 * Site A Observe-Only Probe (RVA 0x291678)
 * Diagnostic experiment for continuous 3D travel distance accumulation.
 * ========================================================================= */
typedef struct {
    uint64_t timestamp;
    uint32_t serial;
    uintptr_t accumulatorAddress;
    float accumulatorBefore;
    float delta;
    float accumulatorAfter;
    float distance3D;
    float scalar;
    uintptr_t component4;
    uintptr_t component5;
} SiteAProbeEvent;

#define SITE_A_PROBE_CAPACITY 1024
static SiteAProbeEvent g_siteAEvents[SITE_A_PROBE_CAPACITY];
static volatile uint32_t g_siteAHead = 0;
static volatile uint32_t g_siteATail = 0;
static volatile uint32_t g_siteADroppedCount = 0;
static volatile uint32_t g_siteAEventCount = 0;
static volatile uint32_t g_siteASerial = 0;
static BOOL g_siteAProbeInstalled = FALSE;
static BOOL g_siteAProbeActive = FALSE;
static BYTE* g_siteAProbeTarget = 0;
QWORD g_siteAProbeContinue = 0;
static BYTE g_siteAProbeOriginal[14];
static char g_siteAProbeLastError[64] = "NONE";
static WCHAR g_siteAProbeCommandPath[1400];
static WCHAR g_siteAProbeStatusPath[1400];
static WCHAR g_siteAProbeJsonlPath[1400];

void architect_siteA_probe_entry(void);

static const BYTE SITE_A_PROBE_EXPECTED[14] = {
    0xF3, 0x0F, 0x58, 0x30,             /* addss xmm6, dword ptr [rax] */
    0xF3, 0x0F, 0x11, 0x30,             /* movss dword ptr [rax], xmm6 */
    0x41, 0xB8, 0x88, 0x00, 0x00, 0x00  /* mov r8d, 0x88 */
};

void architect_siteA_probe_capture(
    uintptr_t accumAddr,
    float delta,
    float dist3D,
    float scalar,
    uintptr_t comp4,
    uintptr_t comp5
) {
    uint32_t nextHead;
    DWORD dwBefore = 0;
    float before = 0.0f;
    uint32_t currentSlot;
    SiteAProbeEvent* evt;

    if (!g_siteAProbeActive) return;

    nextHead = (g_siteAHead + 1) % SITE_A_PROBE_CAPACITY;
    if (nextHead == g_siteATail) {
        _InterlockedIncrement((volatile long*)&g_siteADroppedCount);
        return;
    }

    if (accumAddr && safe_read_u32((const void*)accumAddr, &dwBefore)) {
        before = *(float*)&dwBefore;
    }

    currentSlot = g_siteAHead;
    evt = &g_siteAEvents[currentSlot];
    evt->timestamp = GetTickCount64();
    evt->serial = (uint32_t)_InterlockedIncrement((volatile long*)&g_siteASerial);
    evt->accumulatorAddress = accumAddr;
    evt->accumulatorBefore = before;
    evt->delta = delta;
    evt->accumulatorAfter = before + delta;
    evt->distance3D = dist3D;
    evt->scalar = scalar;
    evt->component4 = comp4;
    evt->component5 = comp5;

    _InterlockedIncrement((volatile long*)&g_siteAEventCount);
    g_siteAHead = nextHead;
}

static BOOL install_siteA_probe(void) {
    DWORD oldProtect = 0, ignored = 0;
    BYTE* target = 0;

    if (g_siteAProbeInstalled) return TRUE;
    if (!g_imageBase) {
        ccopy(g_siteAProbeLastError, sizeof(g_siteAProbeLastError), "IMAGE_BASE_NULL", 16);
        return FALSE;
    }

    target = g_imageBase + 0x291678;
    if (!arch_bytes_equal(target, SITE_A_PROBE_EXPECTED, 14)) {
        ccopy(g_siteAProbeLastError, sizeof(g_siteAProbeLastError), "SIGNATURE_MISMATCH", 19);
        return FALSE;
    }

    mem_copy(g_siteAProbeOriginal, target, 14);
    g_siteAProbeTarget = target;
    g_siteAProbeContinue = (QWORD)(target + 14);

    if (!VirtualProtect(target, 14, PAGE_EXECUTE_READWRITE, &oldProtect)) {
        ccopy(g_siteAProbeLastError, sizeof(g_siteAProbeLastError), "VIRTUAL_PROTECT_RWX_FAILED", 27);
        g_siteAProbeTarget = 0;
        g_siteAProbeContinue = 0;
        return FALSE;
    }

    if (!write_abs_jump_preserve_registers(target, (LPVOID)architect_siteA_probe_entry, 14)) {
        VirtualProtect(target, 14, oldProtect, &ignored);
        ccopy(g_siteAProbeLastError, sizeof(g_siteAProbeLastError), "WRITE_JUMP_FAILED", 18);
        g_siteAProbeTarget = 0;
        g_siteAProbeContinue = 0;
        return FALSE;
    }

    FlushInstructionCache(GetCurrentProcess(), target, 14);
    VirtualProtect(target, 14, oldProtect, &ignored);

    g_siteAProbeInstalled = TRUE;
    ccopy(g_siteAProbeLastError, sizeof(g_siteAProbeLastError), "NONE", 5);
    return TRUE;
}

static BOOL uninstall_siteA_probe(void) {
    DWORD oldProtect = 0, ignored = 0;
    if (!g_siteAProbeInstalled || !g_siteAProbeTarget) return TRUE;

    if (VirtualProtect(g_siteAProbeTarget, 14, PAGE_EXECUTE_READWRITE, &oldProtect)) {
        mem_copy(g_siteAProbeTarget, g_siteAProbeOriginal, 14);
        FlushInstructionCache(GetCurrentProcess(), g_siteAProbeTarget, 14);
        VirtualProtect(g_siteAProbeTarget, 14, oldProtect, &ignored);
    }

    g_siteAProbeInstalled = FALSE;
    g_siteAProbeActive = FALSE;
    g_siteAProbeTarget = 0;
    g_siteAProbeContinue = 0;
    return TRUE;
}

static void flush_siteA_probe_events(void) {
    char line[512];
    DWORD p;
    uint32_t tail = g_siteATail;
    uint32_t head = g_siteAHead;

    while (tail != head) {
        SiteAProbeEvent* evt = &g_siteAEvents[tail];
        p = 0;
        p = append_ascii(line, p, sizeof(line), "{\"timestamp\":");
        p = append_u64_dec(line, p, sizeof(line), evt->timestamp);
        p = append_ascii(line, p, sizeof(line), ",\"serial\":");
        p = append_u64_dec(line, p, sizeof(line), evt->serial);
        p = append_ascii(line, p, sizeof(line), ",\"accumulatorAddress\":\"0x");
        p = append_u64_hex(line, p, sizeof(line), evt->accumulatorAddress);
        p = append_ascii(line, p, sizeof(line), "\",\"accumulatorBefore\":");
        p = append_float(line, p, sizeof(line), evt->accumulatorBefore);
        p = append_ascii(line, p, sizeof(line), ",\"delta\":");
        p = append_float(line, p, sizeof(line), evt->delta);
        p = append_ascii(line, p, sizeof(line), ",\"accumulatorAfter\":");
        p = append_float(line, p, sizeof(line), evt->accumulatorAfter);
        p = append_ascii(line, p, sizeof(line), ",\"distance3D\":");
        p = append_float(line, p, sizeof(line), evt->distance3D);
        p = append_ascii(line, p, sizeof(line), ",\"scalar\":");
        p = append_float(line, p, sizeof(line), evt->scalar);
        p = append_ascii(line, p, sizeof(line), ",\"component4\":\"0x");
        p = append_u64_hex(line, p, sizeof(line), evt->component4);
        p = append_ascii(line, p, sizeof(line), "\",\"component5\":\"0x");
        p = append_u64_hex(line, p, sizeof(line), evt->component5);
        p = append_ascii(line, p, sizeof(line), "\"}\r\n");

        append_file(g_siteAProbeJsonlPath, line, p);
        tail = (tail + 1) % SITE_A_PROBE_CAPACITY;
    }
    g_siteATail = tail;
}

static void write_siteA_probe_status(void) {
    char json[512];
    DWORD p = 0;
    p = append_ascii(json, p, sizeof(json), "{\r\n  \"probeInstalled\": ");
    p = append_ascii(json, p, sizeof(json), g_siteAProbeInstalled ? "true" : "false");
    p = append_ascii(json, p, sizeof(json), ",\r\n  \"probeActive\": ");
    p = append_ascii(json, p, sizeof(json), g_siteAProbeActive ? "true" : "false");
    p = append_ascii(json, p, sizeof(json), ",\r\n  \"probeEventCount\": ");
    p = append_u64_dec(json, p, sizeof(json), g_siteAEventCount);
    p = append_ascii(json, p, sizeof(json), ",\r\n  \"droppedEventCount\": ");
    p = append_u64_dec(json, p, sizeof(json), g_siteADroppedCount);
    p = append_ascii(json, p, sizeof(json), ",\r\n  \"probeLastError\": \"");
    p = append_ascii(json, p, sizeof(json), g_siteAProbeLastError);
    p = append_ascii(json, p, sizeof(json), "\"\r\n}\r\n");

    write_all(g_siteAProbeStatusPath, json, p);
}

static void process_siteA_probe_command(void) {
    char buf[512];
    DWORD bytesRead = 0;
    char action[64];

    if (!file_exists(g_siteAProbeCommandPath)) return;

    bytesRead = read_all(g_siteAProbeCommandPath, buf, sizeof(buf) - 1);
    DeleteFileW(g_siteAProbeCommandPath);
    if (!bytesRead) return;
    buf[bytesRead] = 0;

    action[0] = 0;
    if (json_get_string(buf, bytesRead, "\"action\"", action, sizeof(action)) ||
        json_get_string(buf, bytesRead, "action", action, sizeof(action))) {
        if (ascii_equal(action, "enable")) {
            if (install_siteA_probe()) {
                g_siteAProbeActive = TRUE;
            }
        } else if (ascii_equal(action, "disable")) {
            g_siteAProbeActive = FALSE;
            uninstall_siteA_probe();
        } else if (ascii_equal(action, "reset")) {
            g_siteAHead = 0;
            g_siteATail = 0;
            g_siteADroppedCount = 0;
            g_siteAEventCount = 0;
        }
    }
    flush_siteA_probe_events();
    write_siteA_probe_status();
}
'''

target_anchor = 'static BOOL install_inventory_transfer_probe(void){'
assert target_anchor in code, "Target anchor not found"
code = code.replace(target_anchor, probe_defs + '\n' + target_anchor)

# 2. Add path setup in worker()
path_anchor = 'build_path(g_gameSettingsStatusPath, 1400, g_bridge, L"\\\\game_settings_status.json");'
probe_paths = '''build_path(g_gameSettingsStatusPath, 1400, g_bridge, L"\\\\game_settings_status.json");
    build_path(g_siteAProbeCommandPath, 1400, g_bridge, L"\\\\siteA_probe_command.json");
    build_path(g_siteAProbeStatusPath, 1400, g_bridge, L"\\\\siteA_probe_status.json");
    build_path(g_siteAProbeJsonlPath, 1400, g_bridge, L"\\\\siteA_probe.jsonl");'''

assert path_anchor in code, "Path anchor not found"
code = code.replace(path_anchor, probe_paths)

# 3. Add clean startup file deletions & initial status
startup_anchor = 'DeleteFileW(g_cheatCorrelationCapturePath);'
probe_startup = '''DeleteFileW(g_cheatCorrelationCapturePath);
    DeleteFileW(g_siteAProbeCommandPath);
    DeleteFileW(g_siteAProbeJsonlPath);
    write_siteA_probe_status();'''

assert startup_anchor in code, "Startup anchor not found"
code = code.replace(startup_anchor, probe_startup)

# 4. Add command.json actions
cmd_anchor = '''            } else {
                g_lastCommandFailureReason[0] = 0;
                accepted = TRUE;
                applied = cheat_toggle_glider_stamina();
                verified = applied;
                ok = applied;
            }'''

probe_cmds = '''            } else {
                g_lastCommandFailureReason[0] = 0;
                accepted = TRUE;
                applied = cheat_toggle_glider_stamina();
                verified = applied;
                ok = applied;
            }
        } else if (ascii_equal(action, "diagnostics.siteA_probe.enable")) {
            accepted = TRUE;
            applied = install_siteA_probe();
            if (applied) g_siteAProbeActive = TRUE;
            verified = applied;
            ok = applied;
            if (!applied) {
                ccopy(g_lastCommandFailureReason, sizeof(g_lastCommandFailureReason), g_siteAProbeLastError, cstrlen(g_siteAProbeLastError));
            }
        } else if (ascii_equal(action, "diagnostics.siteA_probe.disable")) {
            accepted = TRUE;
            g_siteAProbeActive = FALSE;
            applied = uninstall_siteA_probe();
            verified = applied;
            ok = applied;
        } else if (ascii_equal(action, "diagnostics.siteA_probe.reset")) {
            accepted = TRUE;
            g_siteAHead = 0;
            g_siteATail = 0;
            g_siteADroppedCount = 0;
            g_siteAEventCount = 0;
            applied = TRUE;
            verified = TRUE;
            ok = TRUE;'''

assert cmd_anchor in code, "Command anchor not found"
code = code.replace(cmd_anchor, probe_cmds, 1)

# 5. Add worker loop periodic processing
loop_anchor = 'if(wroteCorrelation)write_cheat_correlation_status();}'
probe_loop = '''if(wroteCorrelation)write_cheat_correlation_status();}
        process_siteA_probe_command();
        if (g_siteAProbeActive && g_siteAHead != g_siteATail) {
            flush_siteA_probe_events();
            write_siteA_probe_status();
        }'''

assert loop_anchor in code, "Loop anchor not found"
code = code.replace(loop_anchor, probe_loop, 1)

# 6. Add shutdown cleanup
shutdown_anchor = 'cheat_correlation_shutdown();'
probe_shutdown = '''cheat_correlation_shutdown();
    uninstall_siteA_probe();
    flush_siteA_probe_events();
    write_siteA_probe_status();'''

assert shutdown_anchor in code, "Shutdown anchor not found"
code = code.replace(shutdown_anchor, probe_shutdown, 1)

with open('runtime/native/source/ArchitectNativeRuntime.c', 'w', encoding='utf-8') as f:
    f.write(code)

print("Successfully patched ArchitectNativeRuntime.c")
