// A small binary for accessing runfiles
package main

import (
	"fmt"
	"os"

	"github.com/bazelbuild/rules_go/go/runfiles"
)

// Args represents the command-line arguments for the runfiles user binary.
type Args struct {
	// The runfile path to locate (e.g., "workspace/path/to/file.txt").
	runfilePath string
}

// parseArgs parses command-line arguments.
// Exits with status 1 if the arguments are invalid.
func parseArgs() Args {
	if len(os.Args) != 2 {
		fmt.Fprintf(os.Stderr, "Usage: %s <runfile_path>\n", os.Args[0])
		fmt.Fprintf(os.Stderr, "Example: %s workspace/path/to/file.txt\n", os.Args[0])
		os.Exit(1)
	}

	return Args{
		runfilePath: os.Args[1],
	}
}

// main is the entry point.
// It parses command-line arguments, locates the specified runfile using the
// Bazel runfiles API, reads its contents, and prints them to stdout.
func main() {
	args := parseArgs()

	// Create runfiles instance
	r, err := runfiles.New()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to locate runfiles: %v\n", err)
		os.Exit(1)
	}

	// Resolve the runfile path
	resolvedPath, err := r.Rlocation(args.runfilePath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to locate runfile: %s\n%v\n", args.runfilePath, err)
		os.Exit(1)
	}

	if resolvedPath == "" {
		fmt.Fprintf(os.Stderr, "Failed to locate runfile: %s\n", args.runfilePath)
		os.Exit(1)
	}

	// Read and print the contents
	content, err := os.ReadFile(resolvedPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to read file: %s\n%v\n", resolvedPath, err)
		os.Exit(1)
	}

	fmt.Print(string(content))
}
