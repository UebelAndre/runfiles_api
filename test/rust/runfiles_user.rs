//! A small binary for accessing runfiles

use std::env;
use std::fs;
use std::process;

use runfiles::{rlocation, Runfiles};

/// Command-line arguments for the runfiles user binary.
struct Args {
    /// The runfile path to locate (e.g., "workspace/path/to/file.txt").
    rlocationpath: String,
}

impl Args {
    /// Parses command-line arguments.
    fn parse() -> Self {
        let args: Vec<String> = env::args().collect();

        if args.len() != 2 {
            eprintln!("Usage: {} <runfile_path>", args[0]);
            eprintln!("Example: {} workspace/path/to/file.txt", args[0]);
            process::exit(1);
        }

        Args {
            rlocationpath: args[1].clone(),
        }
    }
}

/// Main entry point.
fn main() {
    let args = Args::parse();

    let r = Runfiles::create().expect("Failed to locate runfiles");
    let path = rlocation!(r, &args.rlocationpath)
        .unwrap_or_else(|| panic!("Failed to locate runfile: {}", args.rlocationpath));

    let content = fs::read_to_string(&path)
        .unwrap_or_else(|e| panic!("Failed to read file: {}\n{}", path.display(), e));
    println!("{}", content);
}
