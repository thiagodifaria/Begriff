import numpy as np

def run_monte_carlo_simulation(financial_profile: dict) -> dict:
    """
    Runs a Monte Carlo simulation for investment returns.

    Args:
        financial_profile: A dictionary containing financial parameters.

    Returns:
        A dictionary with the simulation's statistical results.
    """
    initial_capital = financial_profile.get("initial_capital", 0)
    monthly_contribution = financial_profile.get("monthly_contribution", 0)
    years_to_simulate = financial_profile.get("years_to_simulate", 1)
    expected_annual_return = financial_profile.get("expected_annual_return", 0.0)
    annual_volatility = financial_profile.get("annual_volatility", 0.0)
    num_simulations = financial_profile.get("num_simulations", 10000)

    final_values = []

    for _ in range(num_simulations):
        current_value = initial_capital
        for _ in range(years_to_simulate):
            annual_return = np.random.normal(
                loc=expected_annual_return, scale=annual_volatility
            )
            current_value += monthly_contribution * 12
            current_value *= 1 + annual_return
        final_values.append(current_value)

    final_values_np = np.array(final_values)

    results = {
        "mean_value": np.mean(final_values_np),
        "median_value": np.median(final_values_np),
        "std_deviation": np.std(final_values_np),
        "percentile_5": np.percentile(final_values_np, 5),
        "percentile_25": np.percentile(final_values_np, 25),
        "percentile_75": np.percentile(final_values_np, 75),
        "percentile_95": np.percentile(final_values_np, 95),
    }

    return results
