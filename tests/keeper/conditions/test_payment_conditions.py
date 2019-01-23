"""Test PaymentConditions contract."""
from squid_py.keeper.conditions.payment_conditions import PaymentConditions
from tests.resources.tiers import e2e_test, should_run_test

if should_run_test('e2e'):
    payment_conditions = PaymentConditions('PaymentConditions')


@e2e_test
def test_payment_conditions_contract():
    assert payment_conditions
    assert isinstance(payment_conditions, PaymentConditions), \
        f'{payment_conditions} is not instance of PaymentConditions'
