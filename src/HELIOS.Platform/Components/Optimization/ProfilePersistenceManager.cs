using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;

namespace HELIOS.Platform.Components.Optimization
{
    /// <summary>
    /// Manages profile persistence and serialization.
    /// </summary>
    public class ProfilePersistenceManager
    {
        private readonly string _profilesDirectory;
        private readonly JsonSerializerOptions _jsonOptions = new() { WriteIndented = true };

        public ProfilePersistenceManager(string profilesDirectory = null)
        {
            _profilesDirectory = profilesDirectory ?? GetDefaultProfilesDirectory();
            EnsureDirectoryExists();
        }

        /// <summary>
        /// Gets the default profiles directory.
        /// </summary>
        private static string GetDefaultProfilesDirectory()
        {
            var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            return Path.Combine(appDataPath, "HELIOS", "Profiles");
        }

        /// <summary>
        /// Ensures the profiles directory exists.
        /// </summary>
        private void EnsureDirectoryExists()
        {
            if (!Directory.Exists(_profilesDirectory))
                Directory.CreateDirectory(_profilesDirectory);
        }

        /// <summary>
        /// Saves a profile to disk.
        /// </summary>
        public async Task<bool> SaveProfileAsync(OptimizationProfile profile)
        {
            try
            {
                var fileName = $"{profile.Name.Replace(" ", "_")}_{profile.Id}.json";
                var filePath = Path.Combine(_profilesDirectory, fileName);

                var json = JsonSerializer.Serialize(profile, _jsonOptions);
                await File.WriteAllTextAsync(filePath, json);

                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error saving profile: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Loads a profile from disk.
        /// </summary>
        public async Task<OptimizationProfile> LoadProfileAsync(string profileId)
        {
            try
            {
                var files = Directory.GetFiles(_profilesDirectory, $"*{profileId}.json");
                if (files.Length == 0)
                    return null;

                var json = await File.ReadAllTextAsync(files[0]);
                var profile = JsonSerializer.Deserialize<OptimizationProfile>(json);

                return profile;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading profile: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Loads all saved profiles.
        /// </summary>
        public async Task<List<OptimizationProfile>> LoadAllProfilesAsync()
        {
            var profiles = new List<OptimizationProfile>();

            try
            {
                var files = Directory.GetFiles(_profilesDirectory, "*.json");
                
                foreach (var file in files)
                {
                    try
                    {
                        var json = await File.ReadAllTextAsync(file);
                        var profile = JsonSerializer.Deserialize<OptimizationProfile>(json);
                        if (profile != null)
                            profiles.Add(profile);
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"Error loading profile from {file}: {ex.Message}");
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading profiles: {ex.Message}");
            }

            return profiles;
        }

        /// <summary>
        /// Deletes a profile from disk.
        /// </summary>
        public async Task<bool> DeleteProfileAsync(string profileId)
        {
            try
            {
                var files = Directory.GetFiles(_profilesDirectory, $"*{profileId}.json");
                
                foreach (var file in files)
                {
                    File.Delete(file);
                    await Task.Delay(10);
                }

                return files.Length > 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error deleting profile: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Exports a profile to a specified location.
        /// </summary>
        public async Task<bool> ExportProfileAsync(OptimizationProfile profile, string exportPath)
        {
            try
            {
                var json = JsonSerializer.Serialize(profile, _jsonOptions);
                await File.WriteAllTextAsync(exportPath, json);
                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error exporting profile: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Imports a profile from a specified location.
        /// </summary>
        public async Task<OptimizationProfile> ImportProfileAsync(string importPath)
        {
            try
            {
                if (!File.Exists(importPath))
                    return null;

                var json = await File.ReadAllTextAsync(importPath);
                var profile = JsonSerializer.Deserialize<OptimizationProfile>(json);

                if (profile != null)
                {
                    profile.Id = Guid.NewGuid().ToString();
                    await SaveProfileAsync(profile);
                }

                return profile;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error importing profile: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Saves the active profile configuration.
        /// </summary>
        public async Task<bool> SaveActiveProfileAsync(string profileId)
        {
            try
            {
                var configPath = Path.Combine(_profilesDirectory, "active_profile.json");
                var config = new { ProfileId = profileId, Timestamp = DateTime.UtcNow };
                var json = JsonSerializer.Serialize(config, _jsonOptions);
                await File.WriteAllTextAsync(configPath, json);
                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error saving active profile: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Loads the active profile ID.
        /// </summary>
        public async Task<string> LoadActiveProfileIdAsync()
        {
            try
            {
                var configPath = Path.Combine(_profilesDirectory, "active_profile.json");
                if (!File.Exists(configPath))
                    return null;

                var json = await File.ReadAllTextAsync(configPath);
                using var doc = JsonDocument.Parse(json);
                var profileId = doc.RootElement.GetProperty("ProfileId").GetString();

                return profileId;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading active profile: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Saves user preferences.
        /// </summary>
        public async Task<bool> SavePreferencesAsync(Dictionary<string, object> preferences)
        {
            try
            {
                var prefsPath = Path.Combine(_profilesDirectory, "preferences.json");
                var json = JsonSerializer.Serialize(preferences, _jsonOptions);
                await File.WriteAllTextAsync(prefsPath, json);
                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error saving preferences: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Loads user preferences.
        /// </summary>
        public async Task<Dictionary<string, object>> LoadPreferencesAsync()
        {
            try
            {
                var prefsPath = Path.Combine(_profilesDirectory, "preferences.json");
                if (!File.Exists(prefsPath))
                    return new Dictionary<string, object>();

                var json = await File.ReadAllTextAsync(prefsPath);
                var prefs = JsonSerializer.Deserialize<Dictionary<string, object>>(json);

                return prefs ?? new Dictionary<string, object>();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error loading preferences: {ex.Message}");
                return new Dictionary<string, object>();
            }
        }

        /// <summary>
        /// Gets the profiles directory path.
        /// </summary>
        public string GetProfilesDirectory() => _profilesDirectory;

        /// <summary>
        /// Lists all saved profile files.
        /// </summary>
        public string[] ListProfileFiles()
        {
            try
            {
                return Directory.GetFiles(_profilesDirectory, "*.json")
                    .Where(f => !f.EndsWith("active_profile.json") && !f.EndsWith("preferences.json"))
                    .ToArray();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error listing profiles: {ex.Message}");
                return Array.Empty<string>();
            }
        }
    }
}
