package org.bdj.external;

import java.io.*;
import java.net.*;
import org.bdj.Status;
import org.bdj.api.API;
import org.bdj.api.KernelAPI;
import org.bdj.api.NativeInvoke;

/**
 * Cinebreak Shell - remote command shell for the BD-JB5 chain.
 * Runs inside the jailbroken console after the sandbox escape.
 * Listen on :9026, speak simple line commands.
 */
public class CinebreakShell {

    private static final int PORT = 9026;
    private static final String BANNER =
        "Cinebreak Shell 1.0 - kernel R/W over TCP\n" +
        "commands: help | notify <msg> | kread <addr> | kwrite <addr> <val32>\n" +
        "          kdump <addr> <bytes> | kstr <addr> | ping | quit";

    public static void main(String[] args) throws Exception {
        Status.println("cinebreak-shell starting on :" + PORT);
        NativeInvoke.sendNotificationRequest("Cinebreak Shell up on :" + PORT);

        API api = API.getInstance();
        KernelAPI kapi = KernelAPI.getInstance();

        ServerSocket srv = new ServerSocket(PORT);
        Status.println("cinebreak-shell listening");

        while (true) {
            Socket sock = srv.accept();
            try {
                BufferedReader in = new BufferedReader(new InputStreamReader(sock.getInputStream()));
                PrintWriter out = new PrintWriter(sock.getOutputStream(), true);
                out.println(BANNER);
                String line;
                while ((line = in.readLine()) != null) {
                    line = line.trim();
                    if (line.isEmpty()) continue;
                    String[] t = line.split("\\s+");
                    try {
                        if (t[0].equals("quit")) break;
                        else if (t[0].equals("help")) out.println(BANNER);
                        else if (t[0].equals("ping")) out.println("pong");
                        else if (t[0].equals("notify")) {
                            String msg = line.substring("notify".length()).trim();
                            out.println("notify ret=" + NativeInvoke.sendNotificationRequest(msg));
                        } else if (t[0].equals("kread")) {
                            long a = Long.decode(t[1]).longValue();
                            out.println("0x" + Long.toHexString(kapi.kread32(a) & 0xFFFFFFFFL));
                        } else if (t[0].equals("kwrite")) {
                            long a = Long.decode(t[1]).longValue();
                            int v = (int) Long.decode(t[2]).longValue();
                            kapi.kwrite32(a, v);
                            out.println("ok");
                        } else if (t[0].equals("kdump")) {
                            long a = Long.decode(t[1]).longValue();
                            int n = Integer.parseInt(t[2]);
                            StringBuilder sb = new StringBuilder();
                            for (int i = 0; i < n && i < 512; i++) {
                                int b = kapi.kread8(a + i) & 0xFF;
                                sb.append("0123456789abcdef".charAt((b >> 4) & 0xF));
                                sb.append("0123456789abcdef".charAt(b & 0xF));
                                sb.append(' ');
                                if (i % 16 == 15) sb.append('\n');
                            }
                            out.println(sb.toString());
                        } else if (t[0].equals("kstr")) {
                            long a = Long.decode(t[1]).longValue();
                            StringBuilder sb = new StringBuilder();
                            for (int i = 0; i < 256; i++) {
                                int b = kapi.kread8(a + i) & 0xFF;
                                if (b == 0) break;
                                sb.append((char) b);
                            }
                            out.println(sb.toString());
                        } else out.println("unknown: " + t[0]);
                    } catch (Exception e) {
                        out.println("err: " + e);
                    }
                }
            } finally {
                sock.close();
            }
        }
    }
}
