# Debugging and Developer Tools

When running the Dash app in debug mode (via `app.run(debug=True)`), an interactive developer toolbar is embedded in the UI. This toolbar provides real-time insights into callback executions, server requests, and errors without leaving your browser.

## Enabling Debug Mode

```bash
python app.py
# (debug mode is enabled by default in `app.py`)
```

## Opening the Debug Toolbar

In the top-right corner of the dashboard, the **Debug** button (⚙️) appears. Click it to expand the developer panel.

## Errors Tab

The **Errors** tab lists any exceptions raised during callback execution or during page rendering. For each error, it shows:

- **Timestamp**: When the error occurred.
- **Callback ID / Context**: The identity of the callback or page context that triggered the error.
- **Exception Type and Message**: The Python exception and its message.
- **Traceback**: Full stack trace to help identify the source of the problem.

Use the Errors tab to quickly diagnose misconfigurations, invalid inputs, or unexpected edge cases in your callbacks.

## Callbacks Tab

The **Callbacks** tab displays a live log of all callback executions. It includes:

- **Time**: When each callback was invoked.
- **Callback Function/Output ID**: Which callback (by its output component ID) ran.
- **Inputs**: A summary of input values and states passed into the callback.
- **Outputs**: The results or component updates produced by the callback.
- **Duration**: Execution time of the callback, in milliseconds.

Monitoring the Callbacks tab helps you:

- Identify performance bottlenecks by spotting long-running callbacks.
- Trace the data flow through your dashboard by following how inputs propagate to outputs.
- Verify that your callbacks are firing in the expected order.

## Requests Tab

*(Optional)* The **Requests** tab tracks HTTP requests from the browser to the server, including AJAX calls for callbacks. You can inspect payloads, status codes, and response times.

## Best Practices

- Use debug mode during development to catch errors early and optimize callback performance.
- Disable debug mode (`debug=False`) in production to avoid exposing internal details to end users.