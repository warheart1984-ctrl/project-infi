namespace AAES.DropboxWatcherService;

public sealed class ServiceLog
{
    private readonly string _path;
    private readonly object _gate = new();

    public ServiceLog(string path)
    {
        _path = path;
        var directory = Path.GetDirectoryName(_path);
        if (!string.IsNullOrWhiteSpace(directory))
        {
            Directory.CreateDirectory(directory);
        }
    }

    public void Write(string message)
    {
        lock (_gate)
        {
            File.AppendAllText(_path, $"[{DateTimeOffset.UtcNow:O}] {message}{Environment.NewLine}");
        }
    }

    public void WriteLine(string message)
    {
        Write(message);
    }
}
