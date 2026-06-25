using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.Web.WebView2.Core;
using System;
using System.IO;
using System.Threading.Tasks;

namespace OperatorDesktop;

public sealed partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        _ = InitializeWebViewAsync();
    }

    private async Task InitializeWebViewAsync()
    {
        await KernelLauncher.EnsureAsync();
        await OperatorWebView.EnsureCoreWebView2Async();
        var core = OperatorWebView.CoreWebView2;
        if (core is null)
        {
            return;
        }

        var kernelUrl = Environment.GetEnvironmentVariable("OPERATOR_KERNEL_URL") ?? "http://127.0.0.1:8790";
        var lawfulBrainUrl = Environment.GetEnvironmentVariable("OPERATOR_LAWFUL_BRAIN_URL") ?? "http://127.0.0.1:8791";
        var devUrl = Environment.GetEnvironmentVariable("OPERATOR_SURFACE_DEV_URL") ?? "http://127.0.0.1:5173";
        var useDev = string.Equals(Environment.GetEnvironmentVariable("OPERATOR_SURFACE_DEV"), "1", StringComparison.Ordinal);

        if (!useDev)
        {
            var distIndex = Path.Combine(AppContext.BaseDirectory, "operator-surface", "dist", "index.html");
            if (File.Exists(distIndex))
            {
                var uri = new Uri(distIndex);
                OperatorWebView.Source = uri;
            }
            else
            {
                useDev = true;
            }
        }

        if (useDev)
        {
            OperatorWebView.Source = new Uri(devUrl);
        }

        var script =
            "window.__OPERATOR_CONFIG__ = Object.assign(window.__OPERATOR_CONFIG__ || {}, { kernelUrl: " +
            System.Text.Json.JsonSerializer.Serialize(kernelUrl) +
            ", lawfulBrainUrl: " +
            System.Text.Json.JsonSerializer.Serialize(lawfulBrainUrl) +
            " });";
        await core.AddScriptToExecuteOnDocumentCreatedAsync(script);
    }
}
