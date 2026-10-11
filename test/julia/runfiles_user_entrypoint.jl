# A small binary for accessing runfiles.
#
# Implements the subject contract in `CONTRIBUTING.md`. The runfiles module is
# inlined below so the script is self-contained.

# {RUNFILES_LIBRARY}

using .Runfiles: Runfiles

const EXIT_ERROR = 1
const EXIT_NO_RUNFILES = 2
const EXIT_NOT_FOUND = 3

function usage()
    println(stderr, "Usage: runfiles_user.jl [--bench ITERATIONS] <rlocationpath>...")
    println(stderr, "Example: runfiles_user.jl workspace/path/to/file.txt")
end

function main(args::Vector{String})
    bench = nothing
    if length(args) >= 2 && args[1] == "--bench"
        bench = parse(Int, args[2])
        args = args[3:end]
    end
    if isempty(args)
        usage()
        exit(EXIT_ERROR)
    end

    start = time_ns()
    rf = Runfiles.create()
    init_ns = time_ns() - start
    if rf === nothing
        println(stderr, "Failed to locate runfiles")
        exit(EXIT_NO_RUNFILES)
    end

    if bench !== nothing
        start = time_ns()
        for _ in 1:bench, path in args
            Runfiles.rlocation(rf, path)
        end
        lookup_ns = time_ns() - start
        println("{\"init_ns\":$(init_ns),\"lookup_ns\":$(lookup_ns),\"iterations\":$(bench),\"paths\":$(length(args))}")
        return
    end

    for path in args
        resolved = Runfiles.rlocation(rf, path)
        if resolved === nothing || !isfile(resolved)
            println(stderr, "Failed to locate runfile: $(path)")
            exit(EXIT_NOT_FOUND)
        end
        print(read(resolved, String))
    end
end

main(ARGS)
