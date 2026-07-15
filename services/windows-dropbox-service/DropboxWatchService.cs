using System.Diagnostics;
using Microsoft.Extensions.Hosting;

namespace AAES.DropboxWatcherService;

public sealed class DropboxWatchService : BackgroundService
{
    private readonly DropboxServiceConfig _config;
    private readonly ServiceLog _log;

    public DropboxWatchService(DropboxServiceConfig config)
    {
        _config = config;
        _log = new ServiceLog(config.LogPath);
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _log.WriteLine($"service starting for repo: {_config.RepoRoot}");
        _log.WriteLine($"config: {Path.GetFileName(_config.LogPath)}");
        _log.WriteLine(DescribeStartupState(_config.UploadBackend, _config.SyncFolderRoot, HasDropboxToken(), _config.AccountScope, _config.SelectedAccountScope));

        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                await RunWatcherOnce(stoppingToken);
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch (Exception ex)
            {
                _log.WriteLine($"watcher failure: {ex.Message}");
            }

            if (!stoppingToken.IsCancellationRequested)
            {
                await Task.Delay(_config.RestartDelayMs, stoppingToken);
            }
        }

        _log.WriteLine("service stopping");
    }

    private async Task RunWatcherOnce(CancellationToken stoppingToken)
    {
        var processStartInfo = new ProcessStartInfo
        {
            FileName = _config.CorepackExecutable,
            Arguments = _config.CorepackArguments,
            WorkingDirectory = _config.RepoRoot,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };

        processStartInfo.Environment["REPO_PATH"] = _config.RepoRoot;
        processStartInfo.Environment["REPO_DROPBOX_ROOT"] = _config.DropboxRoot;
        processStartInfo.Environment["REPO_DROPBOX_ACCOUNT_SCOPE"] = _config.AccountScope;
        if (!string.IsNullOrWhiteSpace(_config.SelectedAccountScope))
        {
            processStartInfo.Environment["REPO_DROPBOX_SELECTED_ACCOUNT_SCOPE"] = _config.SelectedAccountScope;
        }
        processStartInfo.Environment["REPO_DROPBOX_HISTORY_LIMIT"] = _config.HistoryLimit.ToString();
        processStartInfo.Environment["REPO_DROPBOX_WATCH_DEBOUNCE_MS"] = _config.WatchDebounceMs.ToString();
        processStartInfo.Environment["REPO_DROPBOX_WATCH_MIN_INTERVAL_MS"] = _config.WatchMinIntervalMs.ToString();
        processStartInfo.Environment["REPO_DROPBOX_WATCH_POLL_INTERVAL_MS"] = _config.WatchPollIntervalMs.ToString();
        if (!string.IsNullOrWhiteSpace(_config.SyncFolderRoot))
        {
            processStartInfo.Environment["REPO_DROPBOX_SYNC_FOLDER_ROOT"] = _config.SyncFolderRoot;
        }

        foreach (var keyValue in LoadEnvironmentFile(_config.EnvFile))
        {
            processStartInfo.Environment[keyValue.Key] = keyValue.Value;
        }

        using var process = new Process
        {
            StartInfo = processStartInfo,
            EnableRaisingEvents = true,
        };

        if (!process.Start())
        {
            throw new InvalidOperationException("Dropbox watcher process could not be started.");
        }

        _log.WriteLine($"watcher started with pid {process.Id}");

        var stdoutPump = PumpAsync(process.StandardOutput, "stdout", stoppingToken);
        var stderrPump = PumpAsync(process.StandardError, "stderr", stoppingToken);
        var exitTask = process.WaitForExitAsync(stoppingToken);
        await exitTask;

        if (!process.HasExited)
        {
            return;
        }

        await Task.WhenAll(stdoutPump, stderrPump);

        _log.WriteLine($"watcher exited with code {process.ExitCode}");
    }

    private async Task PumpAsync(StreamReader reader, string streamName, CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            var line = await reader.ReadLineAsync(stoppingToken);
            if (line is null)
            {
                break;
            }

            _log.WriteLine($"[{streamName}] {line}");
        }
    }

    private static IReadOnlyDictionary<string, string> LoadEnvironmentFile(string? envFile)
    {
        if (string.IsNullOrWhiteSpace(envFile) || !File.Exists(envFile))
        {
            return new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        }

        var values = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var rawLine in File.ReadAllLines(envFile))
        {
            var line = rawLine.Trim();
            if (line.Length == 0 || line.StartsWith('#'))
            {
                continue;
            }

            var separatorIndex = line.IndexOf('=');
            if (separatorIndex <= 0)
            {
                continue;
            }

            var key = line[..separatorIndex].Trim();
            var value = line[(separatorIndex + 1)..].Trim();
            if (key.Length > 0)
            {
                values[key] = value;
            }
        }

        return values;
    }

    private static string DescribeBackend(string backend)
    {
        return backend switch
        {
            "api" => "api",
            "api+folder" => "api+folder",
            "folder" => "folder",
            _ => "none",
        };
    }

    private static bool HasDropboxToken()
    {
        return !string.IsNullOrWhiteSpace(Environment.GetEnvironmentVariable("DROPBOX_TOKEN"));
    }

    private static string DescribeStartupState(string backend, string? syncFolderRoot, bool tokenPresent, string accountScope, string? selectedAccountScope)
    {
        var backendDescription = DescribeBackend(backend);
        var folderDescription = string.IsNullOrWhiteSpace(syncFolderRoot) ? "folder=none" : $"folder={syncFolderRoot}";
        var tokenDescription = tokenPresent ? "token=present" : "token=missing";
        var scopeDescription = string.IsNullOrWhiteSpace(accountScope) ? "scope=auto" : $"scope={accountScope}";
        var selectedScopeDescription = string.IsNullOrWhiteSpace(selectedAccountScope) ? "selected=none" : $"selected={selectedAccountScope}";
        return $"dropbox startup | backend={backendDescription} | {folderDescription} | {tokenDescription} | {scopeDescription} | {selectedScopeDescription}";
    }
}
