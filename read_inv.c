#include <iostream>
#include <thread>
#include <vector>
#include <cstring>
#include <glib.h>
#include "outbackbt.h"
#include "dbushelper.h"
#include "utils.h"
#include "inverter.h"

// Assuming `logger` is a global object setup in utils.h
extern Logger logger;

std::vector<std::string> get_btaddr(int argc, char* argv[]) {
    if (argc > 1) {
        std::vector<std::string> btaddr;
        for (int i = 1; i < argc; ++i) {
            btaddr.push_back(argv[i]);
        }
        return btaddr;
    } else {
        return {OUTBACK_ADDRESS};
    }
}

void poll_inverter(GMainLoop* loop, DbusHelper* inverterDevice) {
    std::thread poller([loop, inverterDevice]() {
        inverterDevice->publish_inverter(loop);
    });
    poller.detach();
}

int main(int argc, char* argv[]) {
    logger.info("Starting dbus-btoutback");
    logger.info("dbus-btoutback v" + std::to_string(DRIVER_VERSION) + DRIVER_SUBVERSION);

    std::vector<std::string> btaddr = get_btaddr(argc, argv);

    OutbackBtDev outbackBtDevConnection(btaddr[0]);
    Inverter outbackInverterObject = OutbackBt(outbackBtDevConnection, btaddr[0]);
    outbackBtDevConnection.connect();

    if (!outbackInverterObject) {
        logger.error("ERROR >>> No Inverter connection at " + btaddr[0]);
        return 1;
    }

    outbackInverterObject.log_settings();

    // Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    GMainLoop* mainloop = g_main_loop_new(nullptr, FALSE);

    DbusHelper inverterDevice(outbackInverterObject, 1);

    if (!inverterDevice.setup_vedbus()) {
        logger.error("ERROR >>> Problem with inverter " + btaddr[0]);
        return 1;
    }

    g_timeout_add(outbackInverterObject.poll_interval, [](gpointer data) -> gboolean {
        poll_inverter(static_cast<GMainLoop*>(data), &inverterDevice);
        return TRUE;
    }, mainloop);

    try {
        g_main_loop_run(mainloop);
    } catch (const std::exception& e) {
        logger.error("Caught exception: " + std::string(e.what()));
    }

    return 0;
}
