package org.bdj.external;

import org.bdj.Status;
import org.bdj.api.API;
import org.bdj.api.KernelAPI;
import org.bdj.api.NativeInvoke;

/**
 * Probe payload for BD-JB5 - exercises the full userland API surface.
 * Safe self-tests only: no kernel writes, no risky addresses.
 */
public class Probe {

    public static void main(String[] args) throws Exception {
        Status.println("=== BD-JB5 Probe v1.0 ===");
        Status.println("payload booted inside BD-J sandbox");

        // 1. PS5 on-screen notification
        int nid = NativeInvoke.sendNotificationRequest("Probe payload is alive!");
        Status.println("notification sent: " + nid);

        // 2. Object address roundtrip (userland read primitive)
        try {
            API api = API.getInstance();
            String marker = "BDJ-PROBE-2026";
            long addr = api.addrof(marker);
            Status.println("marker object @ 0x" + Long.toHexString(addr));
            if (addr != 0L) {
                Status.println("userland read primitive: OK");
            }
        } catch (Throwable t) {
            Status.println("userland read probe failed: " + t);
        }

        // 3. Kernel read probe (guarded - safe on failure)
        try {
            KernelAPI k = KernelAPI.getInstance();
            int v = k.kread32(0x0);
            Status.println("kernel kread32(0x0) = 0x" + Integer.toHexString(v));
        } catch (Throwable t) {
            Status.println("kernel probe skipped: " + t);
        }

        // 4. Heartbeat loop over the remote logger
        for (int i = 0; i < 5; i++) {
            Status.println("heartbeat " + i + " ...");
            Thread.sleep(1000);
        }
        Status.println("=== Probe complete ===");
    }
}
