using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;

namespace HELIOS.Platform.Presentation.Views;

public class ModelInfo
{
    public string? Id { get; set; }
    public string? Name { get; set; }
    public string? Description { get; set; }
    public string? Type { get; set; } // LLM, Vision, Audio, Embedding, etc.
    public string? Version { get; set; }
    public long SizeMb { get; set; }
    public bool IsEnabled { get; set; }
    public bool IsInstalled { get; set; }
    public DateTime? LastUsed { get; set; }
    public int? Accuracy { get; set; }
    public double? InferenceSpeedMs { get; set; }
}

public class ActivityLogEntry
{
    public string? Message { get; set; }
    public DateTime Timestamp { get; set; }
}

public class MetricItem
{
    public string? Label { get; set; }
    public string? Value { get; set; }
}

public sealed partial class AiHubPage : Page
{
    private ObservableCollection<ModelInfo> _models = new();
    private ObservableCollection<ActivityLogEntry> _activityLog = new();

    public AiHubPage()
    {
        this.InitializeComponent();
        _ = InitializeAsync();
    }

    private async Task InitializeAsync()
    {
        await LoadModelsAsync();
        await UpdateStatisticsAsync();
    }

    private async Task LoadModelsAsync()
    {
        try
        {
            // Initialize with sample models
            var sampleModels = new[]
            {
                new ModelInfo
                {
                    Id = "llama-2-7b",
                    Name = "Llama 2 7B",
                    Description = "Meta's Llama 2 7 billion parameter model",
                    Type = "LLM",
                    Version = "2.1",
                    SizeMb = 7000,
                    IsEnabled = true,
                    IsInstalled = true,
                    InferenceSpeedMs = 45.2,
                    Accuracy = 92
                },
                new ModelInfo
                {
                    Id = "mistral-7b",
                    Name = "Mistral 7B",
                    Description = "Mistral AI's fast inference model",
                    Type = "LLM",
                    Version = "0.1",
                    SizeMb = 7100,
                    IsEnabled = true,
                    IsInstalled = true,
                    InferenceSpeedMs = 38.5,
                    Accuracy = 90
                },
                new ModelInfo
                {
                    Id = "neural-chat-7b",
                    Name = "Neural Chat 7B",
                    Description = "Intel's optimized chat model",
                    Type = "LLM",
                    Version = "1.3",
                    SizeMb = 7050,
                    IsEnabled = false,
                    IsInstalled = true,
                    InferenceSpeedMs = 50.1,
                    Accuracy = 88
                },
                new ModelInfo
                {
                    Id = "gpt4-turbo",
                    Name = "GPT-4 Turbo",
                    Description = "OpenAI's GPT-4 Turbo model",
                    Type = "LLM",
                    Version = "1.0",
                    SizeMb = 0, // Cloud-based
                    IsEnabled = false,
                    IsInstalled = false,
                    InferenceSpeedMs = 2.5,
                    Accuracy = 98
                },
                new ModelInfo
                {
                    Id = "clip-vit",
                    Name = "CLIP ViT-L",
                    Description = "OpenAI's vision-language model",
                    Type = "Vision",
                    Version = "1.0",
                    SizeMb = 860,
                    IsEnabled = true,
                    IsInstalled = true,
                    InferenceSpeedMs = 25.3,
                    Accuracy = 91
                },
                new ModelInfo
                {
                    Id = "whisper-large",
                    Name = "Whisper Large",
                    Description = "OpenAI's speech recognition model",
                    Type = "Audio",
                    Version = "2.0",
                    SizeMb = 3100,
                    IsEnabled = false,
                    IsInstalled = true,
                    InferenceSpeedMs = 100.5,
                    Accuracy = 96
                }
            };

            _models.Clear();
            foreach (var model in sampleModels)
            {
                _models.Add(model);
            }

            ModelsListView.ItemsSource = _models;
            LogActivity($"Loaded {_models.Count} models");

            await Task.CompletedTask;
        }
        catch (Exception ex)
        {
            LogActivity($"Error loading models: {ex.Message}");
        }
    }

    private async Task UpdateStatisticsAsync()
    {
        try
        {
            var installed = _models.Count(m => m.IsInstalled);
            var active = _models.Count(m => m.IsEnabled);
            var totalGpuMemory = _models.Where(m => m.IsEnabled).Sum(m => m.SizeMb);
            var avgSpeed = _models.Where(m => m.IsEnabled).Average(m => m.InferenceSpeedMs ?? 0);

            InstalledCountText.Text = installed.ToString();
            ActiveCountText.Text = active.ToString();
            GpuMemoryText.Text = $"{totalGpuMemory / 1024} GB";
            GpuMemoryBar.Value = Math.Min(totalGpuMemory / 100, 100); // Assuming 100GB total
            InferenceSpeedText.Text = $"{avgSpeed:F1} ms";

            await Task.CompletedTask;
        }
        catch (Exception ex)
        {
            LogActivity($"Error updating statistics: {ex.Message}");
        }
    }

    private void ModelsListView_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        try
        {
            if (ModelsListView.SelectedItem is ModelInfo model)
            {
                var metrics = new[]
                {
                    new MetricItem { Label = "Type", Value = model.Type },
                    new MetricItem { Label = "Version", Value = model.Version },
                    new MetricItem { Label = "Size", Value = $"{model.SizeMb} MB" },
                    new MetricItem { Label = "Status", Value = model.IsInstalled ? "Installed" : "Not Installed" },
                    new MetricItem { Label = "Accuracy", Value = model.Accuracy.HasValue ? $"{model.Accuracy}%" : "N/A" },
                    new MetricItem { Label = "Inference Speed", Value = model.InferenceSpeedMs.HasValue ? $"{model.InferenceSpeedMs} ms" : "N/A" },
                    new MetricItem { Label = "Last Used", Value = model.LastUsed?.ToString("g") ?? "Never" }
                };

                ModelMetricsControl.ItemsSource = metrics;
                ModelDetailText.Text = model.Description;
                LogActivity($"Selected model: {model.Name}");
            }
        }
        catch (Exception ex)
        {
            LogActivity($"Error selecting model: {ex.Message}");
        }
    }

    private void ModelEnabledToggle_Toggled(object sender, RoutedEventArgs e)
    {
        if (sender is ToggleSwitch toggle && toggle.DataContext is ModelInfo model)
        {
            model.IsEnabled = toggle.IsOn;
            LogActivity($"{(toggle.IsOn ? "Enabled" : "Disabled")} {model.Name}");
            _ = UpdateStatisticsAsync();
        }
    }

    private void RefreshModelsButton_Click(object sender, RoutedEventArgs e)
    {
        LogActivity("Refreshing model list...");
        _ = LoadModelsAsync();
    }

    private void AddModelButton_Click(object sender, RoutedEventArgs e)
    {
        LogActivity("Add model dialog would open");
        // In real implementation, would open dialog to add new model
    }

    private void DownloadModelButton_Click(object sender, RoutedEventArgs e)
    {
        if (ModelsListView.SelectedItem is ModelInfo model)
        {
            LogActivity($"Downloading {model.Name}...");
            // In real implementation, would start download
        }
    }

    private void TestModelButton_Click(object sender, RoutedEventArgs e)
    {
        if (ModelsListView.SelectedItem is ModelInfo model)
        {
            LogActivity($"Testing {model.Name}...");
            // In real implementation, would run test
        }
    }

    private void OptimizeButton_Click(object sender, RoutedEventArgs e)
    {
        if (ModelsListView.SelectedItem is ModelInfo model)
        {
            LogActivity($"Optimizing {model.Name}...");
            // In real implementation, would start optimization
        }
    }

    private void ModelSearchBox_QuerySubmitted(AutoSuggestBox sender, AutoSuggestBoxQuerySubmittedEventArgs args)
    {
        try
        {
            var query = args.QueryText.ToLowerInvariant();
            var filtered = _models.Where(m =>
                m.Name?.ToLowerInvariant().Contains(query) == true ||
                m.Type?.ToLowerInvariant().Contains(query) == true ||
                m.Description?.ToLowerInvariant().Contains(query) == true
            ).ToList();

            ModelsListView.ItemsSource = filtered;
            LogActivity($"Filtered models: {filtered.Count} results");
        }
        catch (Exception ex)
        {
            LogActivity($"Search error: {ex.Message}");
        }
    }

    private void LogActivity(string message)
    {
        _activityLog.Insert(0, new ActivityLogEntry
        {
            Message = message,
            Timestamp = DateTime.Now
        });

        // Keep only last 20 items
        while (_activityLog.Count > 20)
            _activityLog.RemoveAt(_activityLog.Count - 1);

        ActivityLogControl.ItemsSource = _activityLog;
    }
}
