use std::{env, fs, process::{Command, ExitCode}};

const ALLOWED_SCHEMAS: [&str; 3] = ["http://", "https://", "ftp://"];

fn extract_url(content: &str) -> Option<String> {
    let mut in_section = false;

    for line in content.lines() {
        // Strip UTF-8 BOM and whitespace (Windows files often use CRLF)
        let line = line.trim().trim_start_matches('\u{feff}');

        if line.starts_with('[') && line.ends_with(']') {
            in_section = line[1..line.len() - 1]
                .trim()
                .eq_ignore_ascii_case("InternetShortcut");
            continue;
        }

        if !in_section || line.starts_with(';') || line.starts_with('#') {
            continue;
        }

        if let Some((key, value)) = line.split_once('=') {
            if key.trim().eq_ignore_ascii_case("url") {
                let value = value.trim();
                if !value.is_empty() {
                    return Some(value.to_string());
                }
            }
        }
    }
    None
}

fn is_schema_allowed(url: &str) -> bool {
    let lower_url = url.to_ascii_lowercase();
    ALLOWED_SCHEMAS.iter().any(|s| lower_url.starts_with(s))
}

fn main() -> ExitCode {
    let Some(path) = env::args().nth(1) else {
        eprintln!("Usage: open-url file.url");
        return ExitCode::from(2);
    };

    let content = match fs::read(&path) {
        Ok(bytes) => String::from_utf8_lossy(&bytes).into_owned(),
        Err(e) => {
            eprintln!("Cannot read '{path}': {e}");
            return ExitCode::from(1);
        }
    };

    let Some(url) = extract_url(&content) else {
        eprintln!("No URL found in '{path}'");
        return ExitCode::from(1);
    };

    if !is_schema_allowed(&url) {
        eprintln!("Schema not allowed (only http, https, ftp): {url}");
        return ExitCode::from(1);
    }

    match Command::new("xdg-open").arg(&url).spawn() {
        Ok(_) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("Cannot run xdg-open: {e}");
            ExitCode::from(1)
        }
    }
}
