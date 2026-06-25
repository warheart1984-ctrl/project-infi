using Microsoft.UI.Dispatching;
using Microsoft.UI.Xaml;
using System.Threading;

namespace OperatorDesktop;

public partial class App : Application
{
    private Window? _window;

    public App()
    {
        WinRT.ComWrappersSupport.InitializeComWrappers();
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        var context = new DispatcherQueueSynchronizationContext(
            DispatcherQueue.GetForCurrentThread());
        SynchronizationContext.SetSynchronizationContext(context);
        _window = new MainWindow();
        _window.Activate();
    }
}
