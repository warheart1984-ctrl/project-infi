using System;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

namespace OperatorDesktop;

/// <summary>
/// Ensures lawful brain and operator kernel are listening on localhost before the UI loads.
/// </summary>
internal static class KernelLauncher
{
    private static Process? _brainProcess;
    private static Process? _kernelProcess;

    public static async Task EnsureAsync()
    {
        var root = ResolveRepoRoot();
        var workspaceRoot = ResolveWorkspaceRoot();
        var kernelUrl = Environment.GetEnvironmentVariable("OPERATOR_KERNEL_URL") ?? "http://127.0.0.1:8790";
        var brainUrl = Environment.GetEnvironmentVariable("OPERATOR_LAWFUL_BRAIN_URL") ?? "http://127.0.0.1:8791";

        LogStartup($"repo_root={root}");
        LogStartup($"workspace_root={workspaceRoot}");
        LogStartup($"kernel_url={kernelUrl} brain_url={brainUrl}");

        if (await IsReachableAsync(kernelUrl))
        {
            LogStartup("kernel already reachable");
            return;
        }

        var python = ResolvePythonExecutable();
        if (python is null)
        {
            LogStartup(
                "ERROR: no Python found. Install Python 3.11+, set OPERATOR_PYTHON, or rebuild with -BundlePython.");
            return;
        }
        LogStartup($"python={python}");

        if (!await IsReachableAsync(brainUrl))
        {
            _brainProcess = StartPython(python, root, workspaceRoot, "lawful_brain", "-m", "operator_kernel.lawful_brain");
            var brainOk = await WaitForHealthAsync($"{brainUrl.TrimEnd('/')}/health", TimeSpan.FromSeconds(20));
            LogStartup(brainOk ? "lawful_brain healthy" : "WARN: lawful_brain not healthy (kernel may use planner fallback)");
        }

        if (!await IsReachableAsync(kernelUrl))
        {
            _kernelProcess = StartPython(python, root, workspaceRoot, "operator_kernel", "-m", "operator_kernel");
            var kernelOk = await WaitForHealthAsync($"{kernelUrl.TrimEnd('/')}/health", TimeSpan.FromSeconds(25));
            LogStartup(kernelOk ? "operator_kernel healthy" : "ERROR: operator_kernel failed to start — see logs\\operator_kernel.log");
        }
    }

    private static void LogStartup(string message)
    {
        try
        {
            var logsDir = Path.Combine(AppContext.BaseDirectory, "logs");
            Directory.CreateDirectory(logsDir);
            var line = $"{DateTime.UtcNow:O} {message}{Environment.NewLine}";
            File.AppendAllText(Path.Combine(logsDir, "startup.log"), line);
        }
        catch
        {
            // ignore logging failures
        }
        System.Diagnostics.Debug.WriteLine($"OperatorDesktop: {message}");
    }

    private static string ResolveRepoRoot()
    {
        var baseDir = AppContext.BaseDirectory;
        var dir = baseDir;
        for (var i = 0; i < 10; i++)
        {
            if (Directory.Exists(Path.Combine(dir, "operator_kernel")))
            {
                return dir;
            }
            var parent = Directory.GetParent(dir)?.FullName;
            if (string.IsNullOrEmpty(parent) || parent == dir)
            {
                break;
            }
            dir = parent;
        }
        return baseDir;
    }

    private static string ResolveWorkspaceRoot()
    {
        var baseDir = AppContext.BaseDirectory;

        var fromEnv = Environment.GetEnvironmentVariable("AAIS_WORKSPACE_ROOT");
        if (!string.IsNullOrWhiteSpace(fromEnv))
        {
            try
            {
                if (Directory.Exists(fromEnv))
                {
                    return Path.GetFullPath(fromEnv);
                }
            }
            catch
            {
                // ignore invalid env path
            }
        }

        // Published layout always ships workspace\ beside the exe — prefer it over the publish root.
        var packagedWorkspace = Path.Combine(baseDir, "workspace");
        if (Directory.Exists(packagedWorkspace))
        {
            return packagedWorkspace;
        }

        var dir = baseDir;
        for (var i = 0; i < 10; i++)
        {
            if (Directory.Exists(Path.Combine(dir, ".git"))
                || File.Exists(Path.Combine(dir, "app", "main.py")))
            {
                if (!string.Equals(Path.GetFullPath(dir), Path.GetFullPath(baseDir), StringComparison.OrdinalIgnoreCase))
                {
                    return dir;
                }
            }
            var parent = Directory.GetParent(dir)?.FullName;
            if (string.IsNullOrEmpty(parent) || parent == dir)
            {
                break;
            }
            dir = parent;
        }

        try
        {
            Directory.CreateDirectory(packagedWorkspace);
        }
        catch
        {
            // ignore
        }
        return packagedWorkspace;
    }

    private static string? ResolvePythonExecutable()
    {
        var baseDir = AppContext.BaseDirectory;
        var bundled = Path.Combine(baseDir, "python", "python.exe");
        if (File.Exists(bundled))
        {
            return bundled;
        }
        bundled = Path.Combine(baseDir, "python", "python3.exe");
        if (File.Exists(bundled))
        {
            return bundled;
        }

        var fromEnv = Environment.GetEnvironmentVariable("OPERATOR_PYTHON");
        if (!string.IsNullOrWhiteSpace(fromEnv) && File.Exists(fromEnv))
        {
            return fromEnv;
        }

        foreach (var name in new[] { "python", "python3", "py" })
        {
            var found = FindOnPath(name);
            if (found is not null)
            {
                return found;
            }
        }

        return FindWindowsPythonInstall();
    }

    private static string? FindWindowsPythonInstall()
    {
        if (!OperatingSystem.IsWindows())
        {
            return null;
        }

        var candidates = new System.Collections.Generic.List<string>();

        var localApp = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        var programsPython = Path.Combine(localApp, "Programs", "Python");
        if (Directory.Exists(programsPython))
        {
            try
            {
                foreach (var dir in Directory.EnumerateDirectories(programsPython, "Python3*"))
                {
                    var exe = Path.Combine(dir, "python.exe");
                    if (File.Exists(exe))
                    {
                        candidates.Add(exe);
                    }
                }
            }
            catch
            {
                // ignore permission errors
            }
        }

        var programFiles = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
        try
        {
            if (Directory.Exists(programFiles))
            {
                foreach (var dir in Directory.EnumerateDirectories(programFiles, "Python3*"))
                {
                    var exe = Path.Combine(dir, "python.exe");
                    if (File.Exists(exe))
                    {
                        candidates.Add(exe);
                    }
                }
            }
        }
        catch
        {
            // ignore
        }

        if (candidates.Count == 0)
        {
            return null;
        }

        candidates.Sort(StringComparer.OrdinalIgnoreCase);
        candidates.Reverse();
        return candidates[0];
    }

    private static string? FindOnPath(string fileName)
    {
        var pathEnv = Environment.GetEnvironmentVariable("PATH") ?? "";
        foreach (var dir in pathEnv.Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries))
        {
            var full = Path.Combine(dir.Trim(), fileName);
            if (File.Exists(full))
            {
                return full;
            }
            if (OperatingSystem.IsWindows() && File.Exists(full + ".exe"))
            {
                return full + ".exe";
            }
        }
        return null;
    }

    private static Process StartPython(
        string python,
        string workingDir,
        string workspaceRoot,
        string logStem,
        params string[] moduleArgs)
    {
        var psi = new ProcessStartInfo
        {
            WorkingDirectory = workingDir,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
        };

        var fileName = Path.GetFileName(python);
        if (fileName.Equals("py.exe", StringComparison.OrdinalIgnoreCase)
            || fileName.Equals("py", StringComparison.OrdinalIgnoreCase))
        {
            psi.FileName = python;
            psi.ArgumentList.Add("-3");
        }
        else
        {
            psi.FileName = python;
        }

        foreach (var arg in moduleArgs)
        {
            psi.ArgumentList.Add(arg);
        }

        psi.Environment["PYTHONPATH"] = workingDir;
        psi.Environment["PYTHONUNBUFFERED"] = "1";
        psi.Environment["AAIS_WORKSPACE_ROOT"] = workspaceRoot;

        var envConfig = Environment.GetEnvironmentVariable("OPERATOR_KERNEL_CONFIG");
        if (!string.IsNullOrWhiteSpace(envConfig) && File.Exists(envConfig))
        {
            psi.Environment["OPERATOR_KERNEL_CONFIG"] = envConfig;
        }
        else
        {
            var cfg = Path.Combine(workingDir, "operator_kernel.config.yaml");
            if (File.Exists(cfg))
            {
                psi.Environment["OPERATOR_KERNEL_CONFIG"] = cfg;
            }
        }

        var logsDir = Path.Combine(AppContext.BaseDirectory, "logs");
        Directory.CreateDirectory(logsDir);
        var logPath = Path.Combine(logsDir, $"{logStem}.log");
        try
        {
            File.AppendAllText(
                logPath,
                $"--- {DateTime.UtcNow:O} start {string.Join(" ", moduleArgs)} cwd={workingDir} ---{Environment.NewLine}");
        }
        catch
        {
            // ignore
        }

        void AppendLog(string? line)
        {
            if (string.IsNullOrEmpty(line))
            {
                return;
            }
            try
            {
                File.AppendAllText(logPath, line + Environment.NewLine);
            }
            catch
            {
                // ignore
            }
        }

        var process = new Process { StartInfo = psi, EnableRaisingEvents = true };
        process.OutputDataReceived += (_, e) => AppendLog(e.Data);
        process.ErrorDataReceived += (_, e) => AppendLog(e.Data);
        process.Exited += (_, _) =>
        {
            try
            {
                File.AppendAllText(logPath, $"--- exit {process.ExitCode} ---{Environment.NewLine}");
            }
            catch
            {
                // ignore
            }
        };
        process.Start();
        process.BeginOutputReadLine();
        process.BeginErrorReadLine();
        return process;
    }

    private static async Task<bool> IsReachableAsync(string baseUrl)
    {
        var healthUrl = $"{baseUrl.TrimEnd('/')}/health";
        try
        {
            using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(2) };
            var response = await client.GetAsync(healthUrl);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    private static async Task<bool> ProbeHealthUrlAsync(string healthUrl)
    {
        try
        {
            using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(2) };
            var response = await client.GetAsync(healthUrl);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    private static async Task<bool> WaitForHealthAsync(string healthUrl, TimeSpan timeout)
    {
        var deadline = DateTime.UtcNow + timeout;
        while (DateTime.UtcNow < deadline)
        {
            if (await ProbeHealthUrlAsync(healthUrl))
            {
                return true;
            }
            await Task.Delay(500);
        }
        return false;
    }
}
