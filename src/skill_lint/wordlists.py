"""Trigger phrases, generic words, and specificity markers for description analysis."""

TRIGGER_PHRASES: list[str] = [
    "Use when",
    "TRIGGER when",
    "Use this skill whenever",
    "Trigger when user",
    "Use for",
    "Activate when",
    "Use this when",
]

ANTI_TRIGGER_PHRASES: list[str] = [
    "DO NOT TRIGGER",
    "DO NOT use when",
    "Don't use for",
    "Not for",
    "Skip when",
    "Never use for",
    "Don't trigger",
    "Do not use this for",
    "Avoid using when",
    "Not applicable when",
    "Not intended for",
    "This skill is NOT for",
]

GENERIC_WORDS: list[str] = [
    "help", "assist", "code", "write", "create", "manage", "handle",
    "process", "work", "do", "make", "use", "run", "build", "get",
    "set", "update", "fix", "add", "remove", "change", "improve",
    "support", "provide",
]

SPECIFICITY_MARKERS: list[str] = [
    # File extensions
    ".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".json", ".yaml", ".yml",
    ".toml", ".html", ".css", ".scss", ".sql", ".sh", ".bash", ".zsh",
    ".rs", ".go", ".java", ".rb", ".php", ".c", ".cpp", ".h", ".hpp",
    ".pdf", ".docx", ".pptx", ".xlsx", ".csv", ".xml", ".svg", ".png",
    ".jpg", ".gif", ".mp4", ".mp3", ".wav",
    # Tools and frameworks
    "React", "Vue", "Angular", "Next.js", "Nuxt", "Svelte",
    "Django", "Flask", "FastAPI", "Express", "Rails",
    "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis",
    "Docker", "Kubernetes", "Terraform", "AWS", "GCP", "Azure",
    "Git", "GitHub", "GitLab", "Bitbucket",
    "Playwright", "Selenium", "Cypress", "Jest", "pytest",
    "npm", "pip", "cargo", "brew", "apt",
    "Claude", "GPT", "LLM", "API", "REST", "GraphQL", "gRPC",
    "MCP", "SDK", "CLI",
    "Slack", "Discord", "Jira", "Linear", "Notion",
    "Anthropic", "OpenAI",
    "Webpack", "Vite", "esbuild", "Rollup",
    "TypeScript", "Python", "Rust", "Go", "Java", "Ruby",
    "Node.js", "Deno", "Bun",
    "PDF", "Word", "Excel", "PowerPoint",
    "S3", "Lambda", "EC2", "RDS",
    "OAuth", "JWT", "SAML", "SSO",
    "WebSocket", "HTTP", "HTTPS", "SSH", "FTP",
    "JSON", "YAML", "TOML", "XML", "CSV",
    "Markdown", "LaTeX", "RST",
]
