# 🎉 Welcome to Markdown Bowser

This is a **test page** to verify the Markdown preview service.

## Features

- ✅ GitHub-style dark theme
- ✅ Code syntax highlighting
- ✅ Mobile responsive layout
- ✅ Directory browsing
- ✅ Table support

## Code Example

```python
def fibonacci(n):
    """Generate Fibonacci sequence up to n."""
    a, b = 0, 1
    while a < n:
        yield a
        a, b = b, a + b

for num in fibonacci(100):
    print(num)
```

```javascript
const greet = (name) => {
  console.log(`Hello, ${name}! 👋`);
};
greet("Markdown Bowser");
```

## Table Example

| Feature | Status | Notes |
|---------|--------|-------|
| Markdown Rendering | ✅ | Via mistune |
| Code Highlighting | ✅ | Via Pygments |
| Mobile Layout | ✅ | Responsive CSS |
| Auto-start | ✅ | launchd |

## Task List

- [x] Create server
- [x] Add styling
- [x] Deploy service
- [ ] Add more Markdown files!

---

> "The best way to predict the future is to create it." — Peter Drucker
