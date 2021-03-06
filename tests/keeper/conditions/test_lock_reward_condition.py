"""Test PaymentConditions contract."""
from squid_py.keeper.conditions.lock_reward import LockRewardCondition
from tests.resources.tiers import e2e_test

lock_reward_condition = LockRewardCondition('LockRewardCondition')


@e2e_test
def test_lock_reward_condition_contract():
    assert lock_reward_condition
    assert isinstance(lock_reward_condition, LockRewardCondition), \
        f'{lock_reward_condition} is not instance of LockRewardCondition'
