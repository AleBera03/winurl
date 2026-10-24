use std::{env, fs, path::{Path, PathBuf}, process::{Command, ExitCode}};

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

fn normalize_url(url: &str) -> String {
    let url = url.trim();
    if !url.is_empty() && !url.contains("://") {
        format!("https://{url}")
    } else {
        url.to_string()
    }
}

fn url_host(url: &str) -> Option<&str> {
    let (_, rest) = url.split_once("://")?;
    let host = rest.split(['/', '?', '#']).next()?;
    // drop userinfo and port
    let host = host.rsplit('@').next()?.split(':').next()?;
    (!host.is_empty()).then_some(host)
}

fn sanitize_name(name: &str) -> String {
    let name: String = name
        .chars()
        .map(|c| if "<>:\"/\\|?*".contains(c) || c.is_control() { '_' } else { c })
        .collect();
    let name = name.trim().trim_end_matches('.');
    if name.is_empty() { "Link".to_string() } else { name.to_string() }
}

fn unique_path(folder: &Path, name: &str) -> PathBuf {
    let mut path = folder.join(format!("{name}.url"));
    let mut i = 2;
    while path.exists() {
        path = folder.join(format!("{name} ({i}).url"));
        i += 1;
    }
    path
}

/// Create a Windows `.url` shortcut inside `folder`, returning its path.
fn create_weblink(folder: &str, url: &str, name: Option<&str>) -> Result<PathBuf, String> {
    let url = normalize_url(url);
    let host = url_host(&url).filter(|_| is_schema_allowed(&url));
    let Some(host) = host else {
        return Err(format!("Invalid URL (only http, https, ftp): {url}"));
    };
    let name = name.map(str::trim).filter(|n| !n.is_empty()).unwrap_or(host);
    let path = unique_path(Path::new(folder), &sanitize_name(name));
    fs::write(&path, format!("[InternetShortcut]\r\nURL={url}\r\n"))
        .map_err(|e| format!("Cannot write '{}': {e}", path.display()))?;
    Ok(path)
}

fn usage() -> ExitCode {
    eprintln!("Usage: winurl FILE.url");
    eprintln!("       winurl --create FOLDER URL [NAME]");
    ExitCode::from(2)
}

fn main() -> ExitCode {
    let args: Vec<String> = env::args().skip(1).collect();

    if args.first().map(String::as_str) == Some("--create") {
        let (Some(folder), Some(url)) = (args.get(1), args.get(2)) else {
            return usage();
        };
        return match create_weblink(folder, url, args.get(3).map(String::as_str)) {
            Ok(path) => {
                println!("{}", path.display());
                ExitCode::SUCCESS
            }
            Err(e) => {
                eprintln!("{e}");
                ExitCode::from(1)
            }
        };
    }

    let Some(path) = args.first() else {
        return usage();
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
