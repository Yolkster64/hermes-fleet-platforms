using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace HELIOS.Platform.Core.Plugins.Marketplace
{
    /// <summary>
    /// Plugin marketplace for discovering and managing plugins
    /// </summary>
    public class PluginMarketplace
    {
        private readonly List<PluginListing> _listings = new();
        private readonly List<PluginReview> _reviews = new();

        /// <summary>
        /// Submit a plugin to the marketplace
        /// </summary>
        public async Task<SubmissionResult> SubmitPluginAsync(PluginSubmission submission)
        {
            if (string.IsNullOrWhiteSpace(submission.PluginId))
            {
                return SubmissionResult.Error("Plugin ID is required");
            }

            if (_listings.Exists(l => l.PluginId == submission.PluginId))
            {
                return SubmissionResult.Error($"Plugin '{submission.PluginId}' already exists");
            }

            try
            {
                var listing = new PluginListing
                {
                    PluginId = submission.PluginId,
                    Name = submission.Name,
                    Description = submission.Description,
                    Version = submission.Version,
                    Author = submission.Author,
                    License = submission.License,
                    Homepage = submission.Homepage,
                    RepositoryUrl = submission.RepositoryUrl,
                    IconUrl = submission.IconUrl,
                    DownloadUrl = submission.DownloadUrl,
                    Categories = submission.Categories ?? new List<string>(),
                    Tags = submission.Tags ?? new List<string>(),
                    SubmittedAt = DateTime.UtcNow,
                    Status = ListingStatus.Pending,
                    Downloads = 0,
                    Rating = 0,
                    Verified = false
                };

                _listings.Add(listing);
                return await Task.FromResult(SubmissionResult.Success(listing));
            }
            catch (Exception ex)
            {
                return SubmissionResult.Error($"Submission failed: {ex.Message}");
            }
        }

        /// <summary>
        /// Search for plugins
        /// </summary>
        public async Task<List<PluginListing>> SearchAsync(string query, string category = null, int limit = 50)
        {
            var results = new List<PluginListing>();
            var queryLower = query.ToLower();

            foreach (var listing in _listings)
            {
                if (listing.Status != ListingStatus.Published)
                    continue;

                var matches = listing.Name.ToLower().Contains(queryLower) ||
                              listing.Description.ToLower().Contains(queryLower) ||
                              listing.Tags.Exists(t => t.ToLower().Contains(queryLower));

                if (!matches)
                    continue;

                if (!string.IsNullOrEmpty(category) && !listing.Categories.Contains(category))
                    continue;

                results.Add(listing);

                if (results.Count >= limit)
                    break;
            }

            return await Task.FromResult(results);
        }

        /// <summary>
        /// Get plugin by ID
        /// </summary>
        public async Task<PluginListing> GetPluginAsync(string pluginId)
        {
            var listing = _listings.Find(l => l.PluginId == pluginId);
            return await Task.FromResult(listing);
        }

        /// <summary>
        /// Get trending plugins
        /// </summary>
        public async Task<List<PluginListing>> GetTrendingAsync(int limit = 10)
        {
            var trending = _listings
                .FindAll(l => l.Status == ListingStatus.Published)
                .FindAll(l => DateTime.UtcNow - l.SubmittedAt < TimeSpan.FromDays(30))
                .FindAll(l => l.Downloads > 0)
                .Sort((a, b) => b.Downloads.CompareTo(a.Downloads));

            return await Task.FromResult(_listings
                .FindAll(l => l.Status == ListingStatus.Published)
                .FindAll(l => DateTime.UtcNow - l.SubmittedAt < TimeSpan.FromDays(30))
                .FindAll(l => l.Downloads > 0)
                .GetRange(0, Math.Min(limit, _listings.Count)));
        }

        /// <summary>
        /// Get top rated plugins
        /// </summary>
        public async Task<List<PluginListing>> GetTopRatedAsync(int limit = 10)
        {
            var topRated = _listings
                .FindAll(l => l.Status == ListingStatus.Published)
                .FindAll(l => l.Rating >= 4.0);

            topRated.Sort((a, b) => b.Rating.CompareTo(a.Rating));

            return await Task.FromResult(topRated.GetRange(0, Math.Min(limit, topRated.Count)));
        }

        /// <summary>
        /// Get categories
        /// </summary>
        public async Task<List<string>> GetCategoriesAsync()
        {
            var categories = new HashSet<string>();
            foreach (var listing in _listings)
            {
                foreach (var cat in listing.Categories)
                {
                    categories.Add(cat);
                }
            }

            return await Task.FromResult(new List<string>(categories));
        }

        /// <summary>
        /// Submit a review for a plugin
        /// </summary>
        public async Task<ReviewSubmissionResult> SubmitReviewAsync(PluginReview review)
        {
            if (!_listings.Exists(l => l.PluginId == review.PluginId))
            {
                return ReviewSubmissionResult.Error("Plugin not found");
            }

            if (review.Rating < 1 || review.Rating > 5)
            {
                return ReviewSubmissionResult.Error("Rating must be between 1 and 5");
            }

            try
            {
                review.Id = Guid.NewGuid().ToString();
                review.SubmittedAt = DateTime.UtcNow;
                _reviews.Add(review);

                // Update average rating
                UpdatePluginRating(review.PluginId);

                return await Task.FromResult(ReviewSubmissionResult.Success(review));
            }
            catch (Exception ex)
            {
                return ReviewSubmissionResult.Error($"Review submission failed: {ex.Message}");
            }
        }

        /// <summary>
        /// Get reviews for a plugin
        /// </summary>
        public async Task<List<PluginReview>> GetReviewsAsync(string pluginId, int limit = 50)
        {
            var reviews = _reviews
                .FindAll(r => r.PluginId == pluginId)
                .GetRange(0, Math.Min(limit, _reviews.Count));

            reviews.Sort((a, b) => b.SubmittedAt.CompareTo(a.SubmittedAt));

            return await Task.FromResult(reviews);
        }

        /// <summary>
        /// Record a plugin download
        /// </summary>
        public async Task RecordDownloadAsync(string pluginId)
        {
            var listing = _listings.Find(l => l.PluginId == pluginId);
            if (listing != null)
            {
                listing.Downloads++;
                listing.LastDownloadedAt = DateTime.UtcNow;
            }

            await Task.CompletedTask;
        }

        /// <summary>
        /// Verify a plugin
        /// </summary>
        public async Task VerifyPluginAsync(string pluginId)
        {
            var listing = _listings.Find(l => l.PluginId == pluginId);
            if (listing != null)
            {
                listing.Verified = true;
                listing.VerifiedAt = DateTime.UtcNow;
                listing.Status = ListingStatus.Published;
            }

            await Task.CompletedTask;
        }

        /// <summary>
        /// Get plugin statistics
        /// </summary>
        public async Task<MarketplaceStatistics> GetStatisticsAsync()
        {
            var stats = new MarketplaceStatistics
            {
                TotalPlugins = _listings.Count,
                PublishedPlugins = _listings.FindAll(l => l.Status == ListingStatus.Published).Count,
                VerifiedPlugins = _listings.FindAll(l => l.Verified).Count,
                TotalDownloads = _listings.Sum(l => l.Downloads),
                TotalReviews = _reviews.Count,
                AverageRating = _listings.Count > 0 
                    ? _listings.Average(l => l.Rating) 
                    : 0
            };

            return await Task.FromResult(stats);
        }

        private void UpdatePluginRating(string pluginId)
        {
            var listing = _listings.Find(l => l.PluginId == pluginId);
            if (listing == null) return;

            var pluginReviews = _reviews.FindAll(r => r.PluginId == pluginId);
            if (pluginReviews.Count == 0)
            {
                listing.Rating = 0;
                return;
            }

            listing.Rating = pluginReviews.Average(r => r.Rating);
            listing.ReviewCount = pluginReviews.Count;
        }
    }

    /// <summary>
    /// Plugin submission
    /// </summary>
    public class PluginSubmission
    {
        public string PluginId { get; set; }
        public string Name { get; set; }
        public string Description { get; set; }
        public string Version { get; set; }
        public string Author { get; set; }
        public string License { get; set; }
        public string Homepage { get; set; }
        public string RepositoryUrl { get; set; }
        public string IconUrl { get; set; }
        public string DownloadUrl { get; set; }
        public List<string> Categories { get; set; }
        public List<string> Tags { get; set; }
    }

    /// <summary>
    /// Plugin listing in marketplace
    /// </summary>
    public class PluginListing
    {
        public string PluginId { get; set; }
        public string Name { get; set; }
        public string Description { get; set; }
        public string Version { get; set; }
        public string Author { get; set; }
        public string License { get; set; }
        public string Homepage { get; set; }
        public string RepositoryUrl { get; set; }
        public string IconUrl { get; set; }
        public string DownloadUrl { get; set; }
        public List<string> Categories { get; set; }
        public List<string> Tags { get; set; }
        public DateTime SubmittedAt { get; set; }
        public ListingStatus Status { get; set; }
        public int Downloads { get; set; }
        public DateTime? LastDownloadedAt { get; set; }
        public double Rating { get; set; }
        public int ReviewCount { get; set; }
        public bool Verified { get; set; }
        public DateTime? VerifiedAt { get; set; }
    }

    /// <summary>
    /// Plugin review
    /// </summary>
    public class PluginReview
    {
        public string Id { get; set; }
        public string PluginId { get; set; }
        public string Author { get; set; }
        public int Rating { get; set; }
        public string Title { get; set; }
        public string Comment { get; set; }
        public DateTime SubmittedAt { get; set; }
        public int Helpful { get; set; }
        public int Unhelpful { get; set; }
    }

    /// <summary>
    /// Listing status
    /// </summary>
    public enum ListingStatus
    {
        Pending,
        Published,
        Rejected,
        Archived
    }

    /// <summary>
    /// Submission result
    /// </summary>
    public class SubmissionResult
    {
        public bool IsSuccess { get; set; }
        public PluginListing Data { get; set; }
        public string ErrorMessage { get; set; }

        public static SubmissionResult Success(PluginListing listing) =>
            new SubmissionResult { IsSuccess = true, Data = listing };

        public static SubmissionResult Error(string message) =>
            new SubmissionResult { IsSuccess = false, ErrorMessage = message };
    }

    /// <summary>
    /// Review submission result
    /// </summary>
    public class ReviewSubmissionResult
    {
        public bool IsSuccess { get; set; }
        public PluginReview Data { get; set; }
        public string ErrorMessage { get; set; }

        public static ReviewSubmissionResult Success(PluginReview review) =>
            new ReviewSubmissionResult { IsSuccess = true, Data = review };

        public static ReviewSubmissionResult Error(string message) =>
            new ReviewSubmissionResult { IsSuccess = false, ErrorMessage = message };
    }

    /// <summary>
    /// Marketplace statistics
    /// </summary>
    public class MarketplaceStatistics
    {
        public int TotalPlugins { get; set; }
        public int PublishedPlugins { get; set; }
        public int VerifiedPlugins { get; set; }
        public int TotalDownloads { get; set; }
        public int TotalReviews { get; set; }
        public double AverageRating { get; set; }
    }
}
