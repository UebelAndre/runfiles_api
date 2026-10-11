// A small binary for accessing runfiles.
//
// Implements the runfiles_api subject contract; see `README.md`.

package com.runfiles_api.test;

import com.google.devtools.build.runfiles.Runfiles;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.List;

public class RunfilesUser {
    static final int EXIT_ERROR = 1;
    static final int EXIT_NO_RUNFILES = 2;
    static final int EXIT_NOT_FOUND = 3;

    /** The subject is built in the main repository. */
    static final String SOURCE_REPO = "";

    static class Args {
        /** When non-negative, time this many lookups of each path instead of printing content. */
        int benchIterations = -1;

        /** The runfile paths to locate (e.g., "workspace/path/to/file.txt"). */
        List<String> paths;
    }

    static void usage() {
        System.err.println("Usage: RunfilesUser [--bench ITERATIONS] <rlocationpath>...");
        System.err.println("Example: RunfilesUser workspace/path/to/file.txt");
    }

    static Args parseArgs(String[] argv) {
        Args args = new Args();
        List<String> rest = Arrays.asList(argv);

        if (rest.size() >= 2 && rest.get(0).equals("--bench")) {
            try {
                args.benchIterations = Integer.parseInt(rest.get(1));
            } catch (NumberFormatException e) {
                System.err.println("Invalid iteration count: " + rest.get(1));
                usage();
                System.exit(EXIT_ERROR);
            }
            rest = rest.subList(2, rest.size());
        }

        if (rest.isEmpty()) {
            usage();
            System.exit(EXIT_ERROR);
        }

        args.paths = rest;
        return args;
    }

    public static void main(String[] argv) throws IOException {
        Args args = parseArgs(argv);

        long start = System.nanoTime();
        Runfiles runfiles;
        try {
            runfiles = Runfiles.preload(System.getenv()).withSourceRepository(SOURCE_REPO);
        } catch (IOException e) {
            System.err.println("Failed to locate runfiles: " + e.getMessage());
            System.exit(EXIT_NO_RUNFILES);
            return;
        }
        long initNs = System.nanoTime() - start;

        if (args.benchIterations >= 0) {
            long lookupStart = System.nanoTime();
            for (int i = 0; i < args.benchIterations; i++) {
                for (String path : args.paths) {
                    runfiles.rlocation(path);
                }
            }
            long lookupNs = System.nanoTime() - lookupStart;
            System.out.printf(
                    "{\"init_ns\":%d,\"lookup_ns\":%d,\"iterations\":%d,\"paths\":%d}%n",
                    initNs, lookupNs, args.benchIterations, args.paths.size());
            return;
        }

        for (String path : args.paths) {
            String resolved = runfiles.rlocation(path);
            if (resolved == null || resolved.isEmpty()) {
                System.err.println("Failed to locate runfile: " + path);
                System.exit(EXIT_NOT_FOUND);
            }

            Path resolvedPath = Paths.get(resolved);
            if (!Files.isRegularFile(resolvedPath)) {
                System.err.println("Runfile does not exist: " + resolved);
                System.exit(EXIT_NOT_FOUND);
            }

            System.out.print(new String(Files.readAllBytes(resolvedPath), StandardCharsets.UTF_8));
        }
    }
}
