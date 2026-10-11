# A small binary for accessing runfiles.
#
# Implements the subject contract in `CONTRIBUTING.md`. The runfiles library
# is inlined below so the script is self-contained.

# {RUNFILES_LIBRARY}

set EXIT_ERROR 1
set EXIT_NO_RUNFILES 2
set EXIT_NOT_FOUND 3

# The subject is built in the main repository.
set SOURCE_REPO ""

proc usage {} {
    puts stderr "Usage: runfiles_user.tcl \[--bench ITERATIONS\] <rlocationpath>..."
    puts stderr "Example: runfiles_user.tcl workspace/path/to/file.txt"
}

set bench ""
if {[llength $argv] >= 2 && [lindex $argv 0] eq "--bench"} {
    set bench [lindex $argv 1]
    set argv [lrange $argv 2 end]
}
if {[llength $argv] == 0} {
    usage
    exit $EXIT_ERROR
}

set start [clock microseconds]
if {[catch {runfiles::create} rf]} {
    puts stderr "Failed to locate runfiles: $rf"
    exit $EXIT_NO_RUNFILES
}
set init_ns [expr {([clock microseconds] - $start) * 1000}]

if {$bench ne ""} {
    set start [clock microseconds]
    for {set i 0} {$i < $bench} {incr i} {
        foreach path $argv {
            runfiles::rlocation_from $rf $path $SOURCE_REPO
        }
    }
    set lookup_ns [expr {([clock microseconds] - $start) * 1000}]
    puts "{\"init_ns\":$init_ns,\"lookup_ns\":$lookup_ns,\"iterations\":$bench,\"paths\":[llength $argv]}"
    exit 0
}

foreach path $argv {
    set resolved [runfiles::rlocation_from $rf $path $SOURCE_REPO]
    if {$resolved eq "" || ![file isfile $resolved]} {
        puts stderr "Failed to locate runfile: $path"
        exit $EXIT_NOT_FOUND
    }
    set fh [open $resolved rb]
    puts -nonewline [read $fh]
    close $fh
}
exit 0
