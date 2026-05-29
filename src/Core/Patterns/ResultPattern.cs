namespace MonadoBlade.Core.Patterns;

/// <summary>
/// Universal Result pattern for all operations. Eliminates exceptions for expected failures.
/// All tracks use this consistently for operation outcomes.
/// </summary>
public abstract record Result
{
    public sealed record Success : Result;
    public sealed record Failure(string ErrorMessage, Exception Exception = null) : Result;

    public static Result Ok() => new Success();
    public static Result Fail(string message, Exception ex = null) => new Failure(message, ex);

    public bool IsSuccess => this is Success;
    public bool IsFailure => this is Failure;
}


/// <summary>Generic Result&lt;T&gt; for typed operations.</summary>
public abstract record Result<T>
{
    public sealed record Success(T Value) : Result<T>;
    public sealed record Failure(string ErrorMessage, Exception Exception = null) : Result<T>;

    public TResult Match<TResult>(
        Func<T, TResult> onSuccess,
        Func<string, Exception, TResult> onFailure) =>
        this switch
        {
            Success s => onSuccess(s.Value),
            Failure f => onFailure(f.ErrorMessage, f.Exception),
            _ => throw new InvalidOperationException("Unknown Result type")
        };

    public void Match(
        Action<T> onSuccess,
        Action<string, Exception> onFailure) =>
        _ = Match(
            v => { onSuccess(v); return true; },
            (msg, ex) => { onFailure(msg, ex); return true; });

    public bool IsSuccess => this is Success;
    public bool IsFailure => this is Failure;

    public T ValueOrThrow() =>
        Match(
            v => v,
            (msg, ex) => throw new InvalidOperationException(msg, ex));

    public T ValueOrDefault(T defaultValue = default) =>
        Match(v => v, (_, __) => defaultValue);
}


/// <summary>Helper methods for Result pattern.</summary>
public static class ResultExtensions
{
    public static Result<T> ToSuccess<T>(this T value) => new Result<T>.Success(value);
    
    public static Result<T> ToFailure<T>(this ErrorCode code, string message, Exception? ex = null) =>
        new Result<T>.Failure(code, message, ex);
    
    public static Result ToSuccess(this object? value = null) => new Result.Success(value);
    
    public static Result ToFailure(this ErrorCode code, string message, Exception? ex = null) =>
        new Result.Failure(code, message, ex);
}
