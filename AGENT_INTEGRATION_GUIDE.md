# Agent Integration Guide - Use AI Knowledge Base

**For All Phase 1 Agents**

This guide tells you how to USE the AI Knowledge Base and apply learnings to your work.

---

## 📖 What's Available

We have comprehensive AI learnings documented in:
- **AI_KNOWLEDGE_BASE.md** - All patterns, best practices, performance optimizations
- **AI_LEARNING_SYSTEM.md** - How the learning loop works
- **PATTERNS_AND_BEST_PRACTICES.md** - (will be generated during execution)
- **OPTIMIZATIONS_APPLIED.md** - (will be generated during execution)

---

## 🎯 How to Apply to Your Task

### Before Starting Your Work

1. **Read Relevant Sections** of AI_KNOWLEDGE_BASE.md:
   - If GUI/UX task: Read "GUI/UX Patterns" section
   - If Security task: Read "Security Patterns" section
   - If Performance task: Read "Performance Patterns" section
   - If Feature task: Read "Code Quality Patterns" section

2. **Understand the Patterns**:
   - What has worked before?
   - What are the best practices?
   - What should I avoid?

3. **Set Performance Targets**:
   - Memory: < 300 MB idle
   - CPU: < 20% idle
   - Response times: < 100ms for API
   - Database queries: < 50ms

---

## 💻 During Implementation

### Apply These Principles

#### For GUI Work
```csharp
✅ Use Xenblade/Monado theme aesthetic
✅ Target 60 FPS animations
✅ Implement dark/light themes
✅ Use Fluent Design System 3
✅ Provide clear visual feedback
✅ Use toast notifications for alerts
```

#### For Security Work
```csharp
✅ Apply zero-trust architecture
✅ Use defense in depth (multiple layers)
✅ Encrypt transit (TLS) + at-rest (AES)
✅ Log all security events
✅ Validate all inputs
✅ Encode all outputs
```

#### For Performance Work
```csharp
✅ Use async/await by default
✅ Implement connection pooling
✅ Use three-level caching
✅ Apply memory pooling
✅ Use lazy loading
✅ Profile under load
```

#### For Feature Work
```csharp
✅ Apply SOLID principles
✅ Use dependency injection
✅ Use repository pattern for data
✅ Use observer pattern for events
✅ Use modern C# (v12+)
✅ Apply design patterns consistently
```

---

## 📝 Reporting Learnings

### When You Discover Something Useful

**Add to AI_LEARNINGS.md**:
```markdown
## Learning: [Your Discovery]

- **What**: [What did you find/optimize]
- **Where**: [File name, line number, or code section]
- **Why**: [Why is this important]
- **How**: [How to apply it]
- **Impact**: [Performance gain, maintainability, etc.]
- **Code Sample**:
  ```csharp
  // Before
  [bad code]
  
  // After  
  [good code]
  ```
- **Agent**: [Your agent name]
- **Status**: [Applied / Pending]
```

### Example Learning

```markdown
## Learning: LINQ Chain Consolidation

- **What**: Premature ToList() materializes too early
- **Where**: DataService.cs line 145
- **Why**: Causes unnecessary memory allocation
- **How**: Combine LINQ filters before materialization
- **Impact**: ~12% performance improvement on this query
- **Code Sample**:
  ```csharp
  // Before (BAD)
  var results = data.Where(x => x.Active)
                    .ToList()  // ← Unnecessary!
                    .Where(x => x.Score > 100)
                    .ToList();
  
  // After (GOOD)
  var results = data.Where(x => x.Active && x.Score > 100)
                    .ToList();  // ← Single materialization
  ```
- **Agent**: code-quality-fleet
- **Status**: Applied
```

---

## 🔄 The Learning Feedback Loop

### Your Role in the Loop

```
[You Complete Your Work]
    ↓
[Extract Learnings from Your Work]
    ↓
[Document in AI_LEARNINGS.md or report to coordinator]
    ↓
[AI Coordinator Reviews All Learnings]
    ↓
[Patterns Added to PATTERNS_AND_BEST_PRACTICES.md]
    ↓
[Next Batch of Agents Gets Updated Recommendations]
    ↓
[They Apply Your Learnings + Execute Faster/Better]
```

**Your learnings compound across the fleet!**

---

## 📊 Performance Targets by Task Type

### GUI Tasks
```
Target:
- Startup time < 3 seconds
- UI responsiveness: 60 FPS
- Animation smoothness: constant 60 FPS
- Memory: < 250 MB
- Dark/light theme switching < 100ms
```

### Security Tasks
```
Target:
- Zero hardcoded secrets ✅
- All inputs validated ✅
- All outputs encoded ✅
- Audit logging on all security events ✅
- No known vulnerabilities ✅
```

### Feature Tasks
```
Target:
- Unit test coverage > 95%
- Integration test coverage 100%
- Response time < 100ms
- Error handling for all paths
- Comprehensive error messages
```

### Performance Tasks
```
Target:
- Memory < 300 MB idle
- CPU < 20% idle
- API response < 100ms
- Database queries < 50ms
- Network transfer optimized (gzip, deltas)
```

---

## 🎨 Code Quality Standards

### Apply These Everywhere

```csharp
// ✅ Modern C# (v12+)
public record User(
    string Id,
    string Name,
    string Email
);

// ✅ Nullable references enabled
#nullable enable
public string? GetUserName(string id) { ... }

// ✅ Pattern matching
public string GetStatus(User? user) => user switch
{
    null => "No user",
    { Name: "" } => "Empty name",
    { Name: not null } => user.Name
};

// ✅ Init-only properties
public class Config
{
    public string ApiKey { get; init; }
    public string ApiUrl { get; init; }
}

// ✅ Async by default
public async Task<User?> GetUserAsync(string id)
{
    return await _userRepository.GetByIdAsync(id);
}

// ✅ SOLID principles applied
public interface IUserRepository
{
    Task<User?> GetByIdAsync(string id);
}

public class UserService
{
    private readonly IUserRepository _repository;
    
    public UserService(IUserRepository repository)
    {
        _repository = repository;  // Dependency injection
    }
}
```

---

## ⚡ Performance Optimization Checklist

Before marking your task complete, check:

### Memory
- [ ] No memory leaks detected
- [ ] Objects are disposed properly
- [ ] Event handlers are cleaned up
- [ ] Static references don't accumulate

### CPU
- [ ] No tight loops without awaits
- [ ] Polling minimized or eliminated
- [ ] Background tasks are batched
- [ ] Work is prioritized correctly

### I/O
- [ ] Async I/O used throughout
- [ ] Caching implemented where appropriate
- [ ] Connections are pooled
- [ ] Batching reduces round trips

### Database
- [ ] Queries are optimized
- [ ] Indexes are in place
- [ ] Connection pooling is configured
- [ ] N+1 queries eliminated

---

## 🧪 Testing Standards

### Unit Tests
```csharp
[Fact]
public void MyFeature_ValidInput_ReturnsExpected()
{
    // Arrange
    var input = new ValidInput();
    var expected = "expected result";
    
    // Act
    var result = MyFeature(input);
    
    // Assert
    Assert.Equal(expected, result);
}

// Test edge cases
[Theory]
[InlineData(null)]
[InlineData("")]
[InlineData("   ")]
public void MyFeature_EdgeCases_HandledCorrectly(string input)
{
    // Should not throw, should handle gracefully
    Assert.DoesNotThrow(() => MyFeature(input));
}
```

### Target: 95%+ coverage
- All public methods tested
- Happy path tested
- Edge cases tested
- Error conditions tested

---

## 📚 Documentation Standards

When you complete your work, document it:

```markdown
# [Feature Name]

## Overview
[Brief description of what this feature does]

## How to Use
[Step-by-step usage instructions]

## Configuration
[Any config options]

## Examples
[Code examples]

## Troubleshooting
[Common issues and solutions]
```

---

## 🚀 Deployment Checklist

Before marking your task DONE:

- [ ] Code builds with zero errors
- [ ] All tests passing (95%+ unit, 100% integration)
- [ ] No security warnings/vulnerabilities
- [ ] Performance targets met
- [ ] Documentation complete
- [ ] Learnings documented
- [ ] SQL status updated to 'done'
- [ ] Ready for next batch of agents

---

## 💬 Communicating with Other Agents

### Update SQL Learnings Table
```sql
INSERT INTO ai_learnings (id, task_id, learning_type, discovery, optimization, code_pattern, performance_improvement, applied)
VALUES (
    'learning-123',
    'p1-your-task-id',
    'performance',
    'Found premature materialization',
    'Combine LINQ filters before ToList()',
    'data.Where(...).Where(...).ToList()',
    12.5,
    1
);
```

### Report to AI Coordinator
At task completion, include in your final report:
- **Key Learnings**: 3-5 main discoveries
- **Optimizations Applied**: How you improved things
- **Performance Gains**: Measured improvements
- **Patterns Used**: Design patterns applied
- **Recommendations**: For other agents

---

## 🎯 Success Criteria

Your task is complete when:

1. ✅ **Feature implemented** - Works as specified
2. ✅ **Tests passing** - 95%+ unit, 100% integration
3. ✅ **Performance met** - Targets achieved
4. ✅ **Security verified** - No vulnerabilities
5. ✅ **Documentation done** - Clear and complete
6. ✅ **Learnings extracted** - Patterns documented
7. ✅ **SQL updated** - Status marked 'done'
8. ✅ **Build succeeds** - No errors or warnings
9. ✅ **Ready for next** - Can hand off to dependent tasks

---

## 📞 Questions?

If you need clarification on:
- **Patterns**: Check AI_KNOWLEDGE_BASE.md section
- **Learning format**: See "Reporting Learnings" above
- **Performance targets**: See "Performance Targets by Task Type"
- **Code standards**: See "Code Quality Standards"

---

**Apply the knowledge. Learn continuously. Optimize relentlessly.**

*Reference this guide throughout your task execution.*
