"""
Almgren–Chriss Optimal Execution Model Demonstration

This script computes and visualizes the optimal execution schedule under the
Almgren–Chriss framework for various risk aversion parameters.

It generates an interactive HTML file (`docs/almgren_chriss_demo.html`) that
illustrates how different risk aversion levels affect the trajectory of order execution.
"""
import numpy as np
import plotly.graph_objects as go

def optimal_schedule(Q, T, sigma, eta, risk_aversion, steps=100):
    k = np.sqrt(risk_aversion * sigma**2 / eta)
    t = np.linspace(0, T, steps + 1)
    x = Q * np.sinh(k * (T - t)) / np.sinh(k * T)
    v = -np.gradient(x, t)
    return t, x, v

def main():
    Q = 1e6
    T = 1.0
    sigma = 0.2
    eta = 1e-6
    risk_params = [1e-8, 1e-7, 1e-6]

    fig = go.Figure()
    for lam in risk_params:
        t, x, _ = optimal_schedule(Q, T, sigma, eta, lam)
        fig.add_trace(
            go.Scatter(
                x=t,
                y=x,
                name=f"\u03BB={lam:.0e}",
                mode="lines",
                line=dict(width=2),
            )
        )

    fig.update_layout(
        title="Optimal Execution Schedule under Almgren–Chriss Model",
        xaxis_title="Time (normalized)",
        yaxis_title="Shares Remaining",
        template="plotly_dark",
    )

    output_file = "docs/almgren_chriss_demo.html"
    fig.write_html(output_file)
    print(f"Generated interactive demo at {output_file}")

if __name__ == "__main__":
    main()