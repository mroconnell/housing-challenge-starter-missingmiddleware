"""Control-city comparison (docs/tod/CONTROL_CITIES_PLAN.md): parser and estimators on small made-up inputs."""
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from missing_middleware.tod import control_cities as cc

OLD = """Survey,State,6-Digit,County,Place,MSA/,PMSA,Central,Zip,Region,Division,Number of,,Place,,1-unit,,,2-units,,,3-4 units,,,5+ units,,,1-unit rep
Date,Code,ID,Code,Code,CMSA,Code,City,Code,Code,Code,Months Rep,,Name,Bldgs,Units,Value,Bldgs,Units,Value,Bldgs,Units,Value,Bldgs,Units,Value,Bldgs
 
2003,55,572000,079,1645,376,33340,1,53202      ,2,3,12,,Milwaukee,254,254,1,13,26,1,2,8,1,10,618,1,254
"""
NEW = """Survey,State,6-Digit,County,Census Place,FIPS Place,FIPS MCD,Pop,CSA,CBSA,Footnote,Central,Zip,Region,Division,Number of,Place,,1-unit,,,2-units,,,3-4 units,,,5+ units,,,1-unit rep
Date,Code,ID,Code,Code,Code,Code,  ,Code,Code,Code,City,Code,Code,Code,Months Rep,Name,Bldgs,Units,Value,Bldgs,Units,Value,Bldgs,Units,Value,Bldgs,Units,Value,Bldgs
 
2015,27,712600,123,3425,58000 ,58000 ,285068 ,378,33460, ,1,551021634  ,2,4,12,St. Paul,60,60,1,1,2,1,0,0,0,8,861,1,60
"""


class ControlCities(unittest.TestCase):
    def test_parses_old_and_new_headers(self):
        with tempfile.TemporaryDirectory() as d:
            for name, text in (("old.txt", OLD), ("new.txt", NEW)):
                (Path(d) / name).write_text(text)
            old = cc.read_bps_file(Path(d) / "old.txt").iloc[0]
            new = cc.read_bps_file(Path(d) / "new.txt").iloc[0]
        self.assertEqual((old["units"], old["units5"], old["name"]), (254 + 26 + 8 + 618, 618, "Milwaukee"))
        self.assertEqual((new["units"], new["units5"], new["fips_place"], new["cbsa"]), (60 + 2 + 0 + 861, 861, "58000", "33460"))

    def test_did_and_blend(self):
        yrs = list(range(2000, 2006))
        R = pd.DataFrame({y: [1, 1, 2, 3] for y in yrs}, index=["t", "a", "b", "c"], dtype=float)
        R.loc["t", [2003, 2004, 2005]] += 2.0          # reform city gains 2 per 1,000 homes after 2002
        self.assertAlmostEqual(cc.did(R, "t", ["a", "b"], (2000, 2002), (2003, 2005)), 2.0)
        eff, w = cc.synth(R, "t", ["a", "b", "c"], (2000, 2002), (2003, 2005))
        self.assertAlmostEqual(sum(w.values()), 1.0, places=6)
        self.assertAlmostEqual(eff, 2.0, places=6)

    def test_five_year_share(self):
        self.assertAlmostEqual(cc.to_5yr_share(2.0), 1.0)            # 2 per 1,000 a year = 1% over five years
        self.assertAlmostEqual(cc.to_5yr_share(2.0, 400, 320), 1.25)  # county office converted to city homes


if __name__ == "__main__":
    unittest.main()
