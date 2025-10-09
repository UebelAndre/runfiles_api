// A small binary for accessing runfiles

package com.runfiles_api.test;

import com.google.devtools.build.runfiles.Runfiles;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

public class RunfilesUser {
    static class Args {
        String runfilePath;
    }

    static Args parseArgs(String[] args) {
        Args result = new Args();
        if (args.length != 1) {
            System.err.println("Usage: RunfilesUser <runfile_path>");
            System.err.println("Example: RunfilesUser workspace/path/to/file.txt");
            System.exit(1);
        }
        result.runfilePath = args[0];
        return result;
    }

    public static void main(String[] args) {
        Args parsedArgs = parseArgs(args);

        String runfilePath = parsedArgs.runfilePath;

        Runfiles runfiles = null;
        try {
            runfiles = Runfiles.create();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        if (runfiles == null) {
            System.err.println("Failed to create runfiles");
            System.exit(1);
        }

        String resolvedPath = runfiles.rlocation(runfilePath);
        if (resolvedPath == null || resolvedPath.isEmpty()) {
            System.err.println("Failed to locate runfile: " + runfilePath);
            System.exit(1);
        }

        try {
            String content = new String(Files.readAllBytes(Paths.get(resolvedPath)));
            System.out.print(content);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
}
