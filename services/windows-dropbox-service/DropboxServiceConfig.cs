using System.Text.Json;

namespace AAES.DropboxWatcherService;

public sealed record DropboxServiceConfig
{
    public string ServiceName { get; init; } = "AAES-OS Dropbox Watcher";
    public string RepoRoot { get; init; } = string.Empty;
    public string CorepackExecutable { get; init; } = "cmd.exe";
    public string CorepackArguments { get; init; } = "/d /s /c corepack pnpm run dropbox:watch";
    public string? EnvFile { get; init; }
    public string LogPath { get; init; } = string.Empty;
    public string DropboxRoot { get; init; } = "/team";
    public string AccountScope { get; init; } = "auto";
    public string? SelectedAccountScope { get; init; }
    public string? SyncFolderRoot { get; init; }
    public string UploadBackend { get; init; } = "none";
    public int HistoryLimit { get; init; } = 5;
    public int RestartDelayMs { get; init; } = 5000;
    public int WatchDebounceMs { get; init; } = 2500;
    public int WatchMinIntervalMs { get; init; } = 15000;
    public int WatchPollIntervalMs { get; init; } = 5000;

    public static DropboxServiceConfig Load(string configPath)
    {
        if (!File.Exists(configPath))
        {
            throw new FileNotFoundException($"Dropbox service config not found: {configPath}", configPath);
        }

        var json = File.ReadAllText(configPath);
        var config = JsonSerializer.Deserialize<DropboxServiceConfig>(json, new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true,
        });

        if (config is null)
        {
            throw new InvalidOperationException($"Dropbox service config is invalid: {configPath}");
        }

        if (string.IsNullOrWhiteSpace(config.RepoRoot))
        {
            throw new InvalidOperationException("Dropbox service config is missing RepoRoot.");
        }

        if (string.IsNullOrWhiteSpace(config.LogPath))
        {
            throw new InvalidOperationException("Dropbox service config is missing LogPath.");
        }

        return config;
    }
}

public sealed record DropboxServiceArguments(string ConfigPath)
{
    public static DropboxServiceArguments Parse(string[] args)
    {
        var configPath = Environment.GetEnvironmentVariable("AAES_DROPBOX_SERVICE_CONFIG");
        if (!string.IsNullOrWhiteSpace(configPath))
        {
            return new DropboxServiceArguments(configPath);
        }

        for (var index = 0; index < args.Length; index += 1)
        {
            var current = args[index];
            if (string.Equals(current, "--config", StringComparison.OrdinalIgnoreCase) && index + 1 < args.Length)
            {
                return new DropboxServiceArguments(args[index + 1]);
            }
            if (current.StartsWith("--config=", StringComparison.OrdinalIgnoreCase))
            {
                return new DropboxServiceArguments(current["--config=".Length..]);
            }
        }

        throw new InvalidOperationException("Dropbox service config path is required via --config or AAES_DROPBOX_SERVICE_CONFIG.");
    }
}
