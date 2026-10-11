/**
 * @file runfiles_user.cc
 * @brief A small binary for accessing runfiles.
 *
 * Implements the subject contract in `CONTRIBUTING.md`.
 */

#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

#include "rules_cc/cc/runfiles/runfiles.h"

using rules_cc::cc::runfiles::Runfiles;

namespace {

constexpr int kExitError = 1;
constexpr int kExitNoRunfiles = 2;
constexpr int kExitNotFound = 3;

/**
 * @brief Command-line arguments for the runfiles user binary.
 */
struct Args {
    /**
     * @brief When non-negative, time this many lookups of each path instead of
     * printing content.
     */
    long bench_iterations = -1;

    /**
     * @brief The runfile paths to locate (e.g., "workspace/path/to/file.txt").
     */
    std::vector<std::string> paths;
};

void Usage(const char* argv0) {
    std::cerr << "Usage: " << argv0
              << " [--bench ITERATIONS] <rlocationpath>..." << std::endl;
    std::cerr << "Example: " << argv0 << " workspace/path/to/file.txt"
              << std::endl;
}

/**
 * @brief Parses command-line arguments.
 *
 * @note Exits with EXIT_FAILURE if the arguments are invalid.
 */
Args ParseArgs(int argc, char* argv[]) {
    Args args;
    int first_path = 1;

    if (argc >= 3 && std::string(argv[1]) == "--bench") {
        args.bench_iterations = std::strtol(argv[2], nullptr, 10);
        first_path = 3;
    }

    for (int i = first_path; i < argc; ++i) {
        args.paths.emplace_back(argv[i]);
    }

    if (args.paths.empty()) {
        Usage(argv[0]);
        std::exit(kExitError);
    }

    return args;
}

long long ElapsedNs(std::chrono::steady_clock::time_point start) {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
               std::chrono::steady_clock::now() - start)
        .count();
}

}  // namespace

/**
 * @brief Main entry point.
 *
 * @return 0 on success, 2 if runfiles cannot be located, 3 if a runfile
 * cannot be resolved, 1 on any other error.
 */
int main(int argc, char* argv[]) {
    Args args = ParseArgs(argc, argv);

    auto start = std::chrono::steady_clock::now();
    std::string error;
    std::unique_ptr<Runfiles> runfiles(Runfiles::Create(argv[0], &error));
    long long init_ns = ElapsedNs(start);
    if (runfiles == nullptr) {
        std::cerr << "Failed to locate runfiles: " << error << std::endl;
        return kExitNoRunfiles;
    }

    if (args.bench_iterations >= 0) {
        auto lookup_start = std::chrono::steady_clock::now();
        std::size_t sink = 0;
        for (long i = 0; i < args.bench_iterations; ++i) {
            for (const auto& path : args.paths) {
                sink += runfiles->Rlocation(path).size();
            }
        }
        long long lookup_ns = ElapsedNs(lookup_start);
        std::cout << "{\"init_ns\":" << init_ns
                  << ",\"lookup_ns\":" << lookup_ns
                  << ",\"iterations\":" << args.bench_iterations
                  << ",\"paths\":" << args.paths.size() << ",\"sink\":" << sink
                  << "}" << std::endl;
        return EXIT_SUCCESS;
    }

    for (const auto& path : args.paths) {
        std::string resolved = runfiles->Rlocation(path);
        if (resolved.empty()) {
            std::cerr << "Failed to locate runfile: " << path << std::endl;
            return kExitNotFound;
        }

        std::ifstream file(resolved);
        if (!file.is_open()) {
            std::cerr << "Failed to read runfile: " << resolved << std::endl;
            return kExitNotFound;
        }

        std::stringstream buffer;
        buffer << file.rdbuf();
        std::cout << buffer.str();
    }

    return EXIT_SUCCESS;
}
