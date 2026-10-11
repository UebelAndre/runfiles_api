//! A small binary for accessing runfiles.
//!
//! Implements the runfiles_api subject contract; see `README.md`.

use std::env;
use std::fs;
use std::hint::black_box;
use std::process;
use std::time::Instant;

use runfiles::{rlocation, Runfiles};

const EXIT_ERROR: i32 = 1;
const EXIT_NO_RUNFILES: i32 = 2;
const EXIT_NOT_FOUND: i32 = 3;

/// Command-line arguments for the runfiles user binary.
struct Args {
    /// When set, time this many lookups of each path instead of printing content.
    bench_iterations: Option<usize>,

    /// The runfile paths to locate (e.g., "workspace/path/to/file.txt").
    paths: Vec<String>,
}

fn usage() {
    eprintln!("Usage: runfiles_user [--bench ITERATIONS] <rlocationpath>...");
    eprintln!("Example: runfiles_user workspace/path/to/file.txt");
}

impl Args {
    /// Parses command-line arguments.
    fn parse() -> Self {
        let mut rest: Vec<String> = env::args().skip(1).collect();

        let mut bench_iterations = None;
        if rest.len() >= 2 && rest[0] == "--bench" {
            bench_iterations = Some(rest[1].parse().unwrap_or_else(|e| {
                eprintln!("Invalid iteration count `{}`: {}", rest[1], e);
                usage();
                process::exit(EXIT_ERROR);
            }));
            rest.drain(..2);
        }

        if rest.is_empty() {
            usage();
            process::exit(EXIT_ERROR);
        }

        Args {
            bench_iterations,
            paths: rest,
        }
    }
}

/// Main entry point.
fn main() {
    let args = Args::parse();

    let start = Instant::now();
    let r = match Runfiles::create() {
        Ok(r) => r,
        Err(e) => {
            eprintln!("Failed to locate runfiles: {:?}", e);
            process::exit(EXIT_NO_RUNFILES);
        }
    };
    let init_ns = start.elapsed().as_nanos();

    if let Some(iterations) = args.bench_iterations {
        let start = Instant::now();
        for _ in 0..iterations {
            for path in &args.paths {
                black_box(rlocation!(r, path));
            }
        }
        let lookup_ns = start.elapsed().as_nanos();
        println!(
            "{{\"init_ns\":{},\"lookup_ns\":{},\"iterations\":{},\"paths\":{}}}",
            init_ns,
            lookup_ns,
            iterations,
            args.paths.len()
        );
        return;
    }

    for path in &args.paths {
        let Some(resolved) = rlocation!(r, path) else {
            eprintln!("Failed to locate runfile: {}", path);
            process::exit(EXIT_NOT_FOUND);
        };

        match fs::read_to_string(&resolved) {
            Ok(content) => print!("{}", content),
            Err(e) => {
                eprintln!("Failed to read runfile {}: {}", resolved.display(), e);
                process::exit(EXIT_NOT_FOUND);
            }
        }
    }
}
