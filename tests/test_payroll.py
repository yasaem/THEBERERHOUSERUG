import unittest
from payroll import calculate,validate_policy

POLICY={'year':2025,'validated':True,'cnss_rate':4.48,'cnss_ceiling':6000,'amo_rate':2.26,'professional_threshold':78000,'professional_low_rate':35,'professional_high_rate':25,'professional_cap':35000,'family_annual':500,'brackets':[[0,0,0],[40000,10,4000],[60000,20,10000],[80000,30,18000],[100000,34,22000],[180000,37,27400]]}
class MoroccanPayroll(unittest.TestCase):
    def test_low_salary_and_capped_social_contributions(self):
        r=calculate(500000,POLICY,0)
        self.assertEqual(r['cnss'],22400);self.assertEqual(r['amo'],11300)
        self.assertEqual(r['ir'],0);self.assertEqual(r['net'],466300)
        high=calculate(1000000,POLICY,0)
        self.assertEqual(high['cnss'],26880);self.assertEqual(high['amo'],22600)
        self.assertEqual(high['taxable_annual'],8406240)
        self.assertEqual(high['ir'],60156)
        self.assertEqual(high['net'],890364)
    def test_family_relief_and_policy_validation(self):
        self.assertEqual(calculate(1000000,POLICY,2)['ir'],51823)
        with self.assertRaises(ValueError):validate_policy({**POLICY,'validated':False})
        with self.assertRaises(ValueError):validate_policy({**POLICY,'cnss_rate':101})
