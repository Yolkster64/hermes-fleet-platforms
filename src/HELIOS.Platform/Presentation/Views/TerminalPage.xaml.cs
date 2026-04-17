using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using System;
using System.Threading.Tasks;
using HELIOS.Platform.Core.CLI;

namespace HELIOS.Platform.Presentation.Views;

public sealed partial class TerminalPage : Page
{
    private CommandRegistry _commandRegistry = new();

    public TerminalPage()
    {
        this.InitializeComponent();
        _ = InitializeAsync();
    }

    private async Task InitializeAsync()
    {
        try
        {
            HeliosCliCommandsFactory.RegisterAllCommands(_commandRegistry);
            AppendOutput("System initialized with 50+ commands\n");
            await Task.CompletedTask;
        }
        catch (Exception ex)
        {
            AppendOutput($"Error initializing terminal: {ex.Message}\n");
        }
    }

    private void CommandInput_KeyDown(object sender, KeyRoutedEventArgs e)
    {
        if (e.Key == Windows.System.VirtualKey.Enter)
        {
            ExecuteCommand();
            e.Handled = true;
        }
    }

    private void ExecuteButton_Click(object sender, RoutedEventArgs e)
    {
        ExecuteCommand();
    }

    private void ExecuteCommand()
    {
        var command = CommandInput.Text.Trim();
        if (string.IsNullOrEmpty(command))
            return;

        AppendOutput($"> {command}\n");
        CommandInput.Text = "";

        try
        {
            if (command.Equals("clear", StringComparison.OrdinalIgnoreCase))
            {
                OutputText.Text = "> ";
                return;
            }

            var parts = command.Split(' ', StringSplitOptions.RemoveEmptyEntries);
            var commandName = parts[0].ToLowerInvariant();
            var args = parts.Length > 1 ? parts[1..] : Array.Empty<string>();

            var cmd = _commandRegistry.GetCommand(commandName);
            if (cmd != null)
            {
                var result = cmd.Execute(args);
                AppendOutput($"{result}\n");
            }
            else
            {
                AppendOutput($"Command not found: {commandName}\n");
                AppendOutput("Type 'help' for available commands\n");
            }
        }
        catch (Exception ex)
        {
            AppendOutput($"Error: {ex.Message}\n");
        }

        AppendOutput("> ");
    }

    private void QuickCommand_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button button && button.Tag is string command)
        {
            CommandInput.Text = command;
            ExecuteCommand();
        }
    }

    private void AppendOutput(string text)
    {
        OutputText.Text += text;
        // Auto-scroll to end
        DispatcherQueue?.TryEnqueue(() =>
        {
            // Scroll to end (would need ScrollViewer binding)
        });
    }
}
