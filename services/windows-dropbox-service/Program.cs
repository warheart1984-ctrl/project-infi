using AAES.DropboxWatcherService;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

var serviceArguments = DropboxServiceArguments.Parse(args);
var config = DropboxServiceConfig.Load(serviceArguments.ConfigPath);

Host.CreateDefaultBuilder(args)
    .UseWindowsService(options =>
    {
        options.ServiceName = config.ServiceName;
    })
    .ConfigureServices(services =>
    {
        services.AddSingleton(config);
        services.AddHostedService<DropboxWatchService>();
    })
    .Build()
    .Run();
