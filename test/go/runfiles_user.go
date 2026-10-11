// A small binary for accessing runfiles.
//
// Implements the runfiles_api subject contract; see `README.md`.
package main

import (
	"fmt"
	"os"
	"strconv"
	"time"

	"github.com/bazelbuild/rules_go/go/runfiles"
)

const (
	exitError      = 1
	exitNoRunfiles = 2
	exitNotFound   = 3
)

// Args represents the command-line arguments for the runfiles user binary.
type Args struct {
	// When non-negative, time this many lookups of each path instead of printing content.
	benchIterations int

	// The runfile paths to locate (e.g., "workspace/path/to/file.txt").
	paths []string
}

func usage() {
	fmt.Fprintf(os.Stderr, "Usage: %s [--bench ITERATIONS] <rlocationpath>...\n", os.Args[0])
	fmt.Fprintf(os.Stderr, "Example: %s workspace/path/to/file.txt\n", os.Args[0])
}

// parseArgs parses command-line arguments.
// Exits with status 1 if the arguments are invalid.
func parseArgs() Args {
	args := Args{benchIterations: -1}
	rest := os.Args[1:]

	if len(rest) >= 2 && rest[0] == "--bench" {
		n, err := strconv.Atoi(rest[1])
		if err != nil {
			fmt.Fprintf(os.Stderr, "Invalid iteration count %q: %v\n", rest[1], err)
			usage()
			os.Exit(exitError)
		}
		args.benchIterations = n
		rest = rest[2:]
	}

	if len(rest) == 0 {
		usage()
		os.Exit(exitError)
	}

	args.paths = rest
	return args
}

// main is the entry point.
func main() {
	args := parseArgs()

	start := time.Now()
	r, err := runfiles.New()
	initNs := time.Since(start).Nanoseconds()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to locate runfiles: %v\n", err)
		os.Exit(exitNoRunfiles)
	}

	if args.benchIterations >= 0 {
		lookupStart := time.Now()
		for i := 0; i < args.benchIterations; i++ {
			for _, path := range args.paths {
				_, _ = r.Rlocation(path)
			}
		}
		lookupNs := time.Since(lookupStart).Nanoseconds()
		fmt.Printf("{\"init_ns\":%d,\"lookup_ns\":%d,\"iterations\":%d,\"paths\":%d}\n",
			initNs, lookupNs, args.benchIterations, len(args.paths))
		return
	}

	for _, path := range args.paths {
		resolved, err := r.Rlocation(path)
		if err != nil || resolved == "" {
			fmt.Fprintf(os.Stderr, "Failed to locate runfile: %s\n%v\n", path, err)
			os.Exit(exitNotFound)
		}

		content, err := os.ReadFile(resolved)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Failed to read runfile: %s\n%v\n", resolved, err)
			os.Exit(exitNotFound)
		}
		fmt.Print(string(content))
	}
}
