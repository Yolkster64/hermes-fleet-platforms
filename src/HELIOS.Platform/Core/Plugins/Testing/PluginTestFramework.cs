using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using HELIOS.Platform.Core.Plugins.Abstractions;

namespace HELIOS.Platform.Core.Plugins.Testing
{
    /// <summary>
    /// Test framework for plugin testing
    /// </summary>
    public class PluginTestFramework
    {
        private readonly List<PluginTestCase> _testCases = new();
        private readonly List<TestResult> _results = new();

        /// <summary>
        /// Register a test case
        /// </summary>
        public void RegisterTestCase(PluginTestCase testCase)
        {
            _testCases.Add(testCase);
        }

        /// <summary>
        /// Run all test cases
        /// </summary>
        public async Task<TestRunResult> RunAllTestsAsync()
        {
            var result = new TestRunResult { StartTime = DateTime.UtcNow };
            _results.Clear();

            foreach (var testCase in _testCases)
            {
                var testResult = await RunTestCaseAsync(testCase);
                _results.Add(testResult);
                result.Results.Add(testResult);
            }

            result.EndTime = DateTime.UtcNow;
            result.CalculateSummary();

            return result;
        }

        /// <summary>
        /// Run a single test case
        /// </summary>
        public async Task<TestResult> RunTestCaseAsync(PluginTestCase testCase)
        {
            var result = new TestResult
            {
                TestName = testCase.Name,
                StartTime = DateTime.UtcNow
            };

            try
            {
                // Setup
                if (testCase.Setup != null)
                {
                    await testCase.Setup();
                }

                // Execute
                await testCase.Execute();

                // Assert
                if (testCase.Assert != null)
                {
                    testCase.Assert();
                }

                result.Status = TestStatus.Passed;
            }
            catch (AssertionException ex)
            {
                result.Status = TestStatus.Failed;
                result.ErrorMessage = ex.Message;
                result.StackTrace = ex.StackTrace;
            }
            catch (Exception ex)
            {
                result.Status = TestStatus.Error;
                result.ErrorMessage = ex.Message;
                result.StackTrace = ex.StackTrace;
            }
            finally
            {
                // Cleanup
                if (testCase.Cleanup != null)
                {
                    try
                    {
                        await testCase.Cleanup();
                    }
                    catch { }
                }

                result.EndTime = DateTime.UtcNow;
            }

            return result;
        }

        /// <summary>
        /// Get test results
        /// </summary>
        public List<TestResult> GetResults() => new List<TestResult>(_results);
    }

    /// <summary>
    /// Plugin test case
    /// </summary>
    public class PluginTestCase
    {
        public string Name { get; set; }
        public string Description { get; set; }
        public Func<Task> Setup { get; set; }
        public Func<Task> Execute { get; set; }
        public Action Assert { get; set; }
        public Func<Task> Cleanup { get; set; }
    }

    /// <summary>
    /// Test result
    /// </summary>
    public class TestResult
    {
        public string TestName { get; set; }
        public TestStatus Status { get; set; }
        public string ErrorMessage { get; set; }
        public string StackTrace { get; set; }
        public DateTime StartTime { get; set; }
        public DateTime EndTime { get; set; }

        public TimeSpan Duration => EndTime - StartTime;
        public bool IsSuccess => Status == TestStatus.Passed;
    }

    /// <summary>
    /// Test run result
    /// </summary>
    public class TestRunResult
    {
        public DateTime StartTime { get; set; }
        public DateTime EndTime { get; set; }
        public List<TestResult> Results { get; } = new();

        public int TotalTests => Results.Count;
        public int PassedTests { get; private set; }
        public int FailedTests { get; private set; }
        public int ErrorTests { get; private set; }
        public double SuccessRate { get; private set; }

        public TimeSpan TotalDuration => EndTime - StartTime;

        public void CalculateSummary()
        {
            PassedTests = Results.FindAll(r => r.Status == TestStatus.Passed).Count;
            FailedTests = Results.FindAll(r => r.Status == TestStatus.Failed).Count;
            ErrorTests = Results.FindAll(r => r.Status == TestStatus.Error).Count;
            SuccessRate = TotalTests > 0 ? (double)PassedTests / TotalTests * 100 : 0;
        }

        public override string ToString()
        {
            return $"Tests: {TotalTests}, Passed: {PassedTests}, Failed: {FailedTests}, Errors: {ErrorTests}, Success Rate: {SuccessRate:F2}%";
        }
    }

    /// <summary>
    /// Test status
    /// </summary>
    public enum TestStatus
    {
        Passed,
        Failed,
        Error,
        Skipped
    }

    /// <summary>
    /// Assertion exception
    /// </summary>
    public class AssertionException : Exception
    {
        public AssertionException(string message) : base(message) { }
    }

    /// <summary>
    /// Assertion utilities
    /// </summary>
    public static class Assert
    {
        public static void IsTrue(bool condition, string message = "Assertion failed")
        {
            if (!condition)
                throw new AssertionException(message);
        }

        public static void IsFalse(bool condition, string message = "Assertion failed")
        {
            if (condition)
                throw new AssertionException(message);
        }

        public static void AreEqual<T>(T expected, T actual, string message = "Values are not equal")
        {
            if (!Equals(expected, actual))
                throw new AssertionException($"{message}. Expected: {expected}, Actual: {actual}");
        }

        public static void AreNotEqual<T>(T expected, T actual, string message = "Values are equal")
        {
            if (Equals(expected, actual))
                throw new AssertionException(message);
        }

        public static void IsNotNull(object value, string message = "Value is null")
        {
            if (value == null)
                throw new AssertionException(message);
        }

        public static void IsNull(object value, string message = "Value is not null")
        {
            if (value != null)
                throw new AssertionException(message);
        }

        public static void Throws<T>(Action action, string message = "Exception not thrown") where T : Exception
        {
            try
            {
                action();
                throw new AssertionException(message);
            }
            catch (T) { }
        }
    }

    /// <summary>
    /// Mock plugin context for testing
    /// </summary>
    public class MockPluginContext : IPluginContext
    {
        private readonly Dictionary<string, object> _services = new();

        public IPluginConfiguration Configuration { get; }
        public IServiceProvider ServiceProvider { get; }
        public IPluginLogger Logger { get; }

        public MockPluginContext()
        {
            Configuration = new PluginConfiguration();
            ServiceProvider = new MockServiceProvider();
            Logger = new MockPluginLogger();
        }

        public IPlugin GetPlugin(string pluginId) => null;
        public void RegisterService(string serviceName, object serviceInstance) => _services[serviceName] = serviceInstance;
        public object GetService(string serviceName) => _services.TryGetValue(serviceName, out var svc) ? svc : null;
        public async Task PublishEventAsync(string eventName, object eventData) => await Task.CompletedTask;
        public void SubscribeToEvent(string eventName, Func<object, Task> handler) { }
    }

    /// <summary>
    /// Mock service provider
    /// </summary>
    public class MockServiceProvider : IServiceProvider
    {
        private readonly Dictionary<Type, object> _services = new();

        public object GetService(Type serviceType) => _services.TryGetValue(serviceType, out var svc) ? svc : null;
        public void RegisterService<T>(T instance) => _services[typeof(T)] = instance;
    }

    /// <summary>
    /// Mock plugin logger
    /// </summary>
    public class MockPluginLogger : IPluginLogger
    {
        public List<string> LogMessages { get; } = new();

        public void Debug(string message) => LogMessages.Add($"[DEBUG] {message}");
        public void Info(string message) => LogMessages.Add($"[INFO] {message}");
        public void Warning(string message) => LogMessages.Add($"[WARN] {message}");
        public void Error(string message, Exception ex = null) => LogMessages.Add($"[ERROR] {message}");
        public void Critical(string message, Exception ex = null) => LogMessages.Add($"[CRITICAL] {message}");
    }

    /// <summary>
    /// Plugin integration test helper
    /// </summary>
    public class PluginIntegrationTestHelper
    {
        private readonly List<IPlugin> _plugins = new();

        /// <summary>
        /// Create and initialize a plugin for testing
        /// </summary>
        public async Task<T> CreateTestPluginAsync<T>() where T : IPlugin, new()
        {
            var plugin = new T();
            var context = new MockPluginContext();
            await plugin.InitializeAsync(context);
            _plugins.Add(plugin);
            return plugin;
        }

        /// <summary>
        /// Cleanup all test plugins
        /// </summary>
        public async Task CleanupAsync()
        {
            foreach (var plugin in _plugins)
            {
                try
                {
                    if (plugin.State == PluginState.Running)
                    {
                        await plugin.StopAsync();
                    }
                    plugin.Dispose();
                }
                catch { }
            }
            _plugins.Clear();
        }
    }
}
