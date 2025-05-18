import numpy as np
import pytest

from models.slippage_model import estimate_slippage
from models.market_impact_model import almgren_chriss_impact
from models.maker_taker_model import predict_maker_proportion


def test_estimate_slippage_default():
    assert estimate_slippage(spread=0.1, quantity=10) == pytest.approx(1.0)


def test_estimate_slippage_with_coefficient():
    params = {'coefficient': 2.5}
    expected = 2.5 * 0.2 * 5
    assert estimate_slippage(spread=0.2, quantity=5, model_params=params) == pytest.approx(expected)


def test_almgren_chriss_impact_simple_case():
    # Using parameters where manual calculation is straightforward
    quantity = 10.0
    time_horizon = 2.0
    alpha = beta = 1.0
    gamma = eta = 1.0
    volatility = 2.0
    risk_aversion = 0.5

    # temp_impact = 1*(10/2)**1 = 5
    # perm_impact = 1*(10/2)**1 = 5
    # risk_term = 0.5*0.5*(2**2)*(10**2)/2 = 50
    expected = 5 + 5 + 50

    result = almgren_chriss_impact(
        quantity=quantity,
        time_horizon=time_horizon,
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        eta=eta,
        volatility=volatility,
        risk_aversion=risk_aversion,
    )
    assert result == pytest.approx(expected)


def test_predict_maker_proportion_default():
    # Default model yields probability 0.5 for any feature vector
    features = np.array([1.0, 2.0, 3.0])
    prob = predict_maker_proportion(features)
    assert prob == pytest.approx(0.5)


def test_predict_maker_proportion_with_params():
    features = np.array([1.0, -1.0])
    params = {'weights': np.array([2.0, -2.0]), 'bias': 0.5}
    # logits = 2*1 + (-2)*(-1) + 0.5 = 2 + 2 + 0.5 = 4.5
    expected_prob = 1.0 / (1.0 + np.exp(-4.5))
    prob = predict_maker_proportion(features, model_params=params)
    assert prob == pytest.approx(expected_prob)