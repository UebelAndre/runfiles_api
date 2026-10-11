#!/usr/bin/perl
# A small binary for accessing runfiles.
#
# Implements the subject contract in `CONTRIBUTING.md`. The runfiles library
# is inlined below so the script is self-contained.

# {RUNFILES_LIBRARY}

package main;

use strict;
use warnings;
use Time::HiRes ();

use constant EXIT_ERROR       => 1;
use constant EXIT_NO_RUNFILES => 2;
use constant EXIT_NOT_FOUND   => 3;

# The subject is built in the main repository.
use constant SOURCE_REPO => '';

sub usage {
    print STDERR "Usage: $0 [--bench ITERATIONS] <rlocationpath>...\n";
    print STDERR "Example: $0 workspace/path/to/file.txt\n";
}

sub now_ns { return Time::HiRes::time() * 1e9; }

my $bench;
if ( @ARGV >= 2 && $ARGV[0] eq '--bench' ) {
    shift @ARGV;
    $bench = shift @ARGV;
}
if ( !@ARGV ) {
    usage();
    exit EXIT_ERROR;
}

my $start   = now_ns();
my $r       = Runfiles->create();
my $init_ns = int( now_ns() - $start );

# `create` always returns an object; one with neither a directory nor a
# manifest means nothing was discovered.
if ( !defined $r->{runfiles_dir} && !defined $r->{manifest_file} ) {
    print STDERR "Failed to locate runfiles\n";
    exit EXIT_NO_RUNFILES;
}

if ( defined $bench ) {
    $start = now_ns();
    for ( 1 .. $bench ) {
        for my $path (@ARGV) {
            $r->rlocation( $path, SOURCE_REPO );
        }
    }
    my $lookup_ns = int( now_ns() - $start );
    printf "{\"init_ns\":%d,\"lookup_ns\":%d,\"iterations\":%d,\"paths\":%d}\n",
        $init_ns, $lookup_ns, $bench, scalar @ARGV;
    exit 0;
}

for my $path (@ARGV) {
    my $resolved = $r->rlocation( $path, SOURCE_REPO );
    if ( !defined $resolved || !-f $resolved ) {
        print STDERR "Failed to locate runfile: $path\n";
        exit EXIT_NOT_FOUND;
    }
    open my $fh, '<:raw', $resolved or do {
        print STDERR "Failed to read runfile $resolved: $!\n";
        exit EXIT_NOT_FOUND;
    };
    local $/;
    print <$fh>;
    close $fh;
}
exit 0;
