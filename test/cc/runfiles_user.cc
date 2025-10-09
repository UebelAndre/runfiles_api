/**
 * @file runfiles_user.cc
 * @brief A small binary for accessing runfiles
 */

#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

#include "rules_cc/cc/runfiles/runfiles.h"

using rules_cc::cc::runfiles::Runfiles;

/**
 * @brief Command-line arguments for the runfiles user binary.
 */
struct Args {
    /**
     * @brief The runfile path to locate (e.g., "workspace/path/to/file.txt").
     */
    std::string runfile_path;
};

/**
 * @brief Parses command-line arguments.
 *
 * @param argc The number of command-line arguments.
 * @param argv The command-line argument array.
 * @return Parsed arguments structure.
 *
 * @note Exits with EXIT_FAILURE if the arguments are invalid.
 */
Args parse_args(int argc, char* argv[]) {
    Args args;
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <runfile_path>" << std::endl;
        std::cerr << "Example: " << argv[0] << " workspace/path/to/file.txt"
                  << std::endl;
        std::exit(EXIT_FAILURE);
    }
    args.runfile_path = argv[1];
    return args;
}

/**
 * @brief Main entry point.
 *
 * Parses command-line arguments, locates the specified runfile using the Bazel
 * runfiles API, reads its contents, and prints them to stdout.
 *
 * @param argc The number of command-line arguments.
 * @param argv The command-line argument array.
 * @return EXIT_SUCCESS on success, EXIT_FAILURE on failure.
 */
int main(int argc, char* argv[]) {
    Args args = parse_args(argc, argv);

    std::string runfile_path = args.runfile_path;

    // Create runfiles instance
    std::string error;
    std::unique_ptr<Runfiles> runfiles(Runfiles::Create(argv[0], &error));
    if (runfiles == nullptr) {
        std::cerr << "Failed to locate runfiles: " << error << std::endl;
        return EXIT_FAILURE;
    }

    // Resolve the runfile path
    std::string resolved_path = runfiles->Rlocation(runfile_path);
    if (resolved_path.empty()) {
        std::cerr << "Failed to locate runfile: " << runfile_path << std::endl;
        return EXIT_FAILURE;
    }

    // Read and print the contents
    std::ifstream file(resolved_path);
    if (!file.is_open()) {
        std::cerr << "Failed to read file: " << resolved_path << std::endl;
        return EXIT_FAILURE;
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    std::cout << buffer.str();

    return EXIT_SUCCESS;
}
